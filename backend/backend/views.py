from django.http import JsonResponse, HttpResponse
import pandas as pd
import ssl
import json
import os
import base64
import time

# https://github.com/xavctn/img2table
from img2table.document import Image
from img2table.ocr import AzureOCR

from django.views.decorators.csrf import csrf_exempt
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def documentation(request):
    print(request)
    return HttpResponse("Table Catcher Documentation page. For testing if server works, for Documentation. ")


def test_connection(request):
    print(request)
    return JsonResponse({'check_connection': 'connected'})


"""
def get_data(request):

    #http://127.0.0.1:8000/get/?topic=https://coinmarketcap.com/
    #This works by URL query parameter.
    #But, we better send POST request from extension to backend like scan_tables() function below.
    
    topic = request.GET.get('topic', None)
    print('Topic:', topic)

    data = {
        'input': topic,
        'table_data': scrape_tables(topic)
    }
    print('Json Data to be sent: ', data)
    return JsonResponse(data)
"""


@csrf_exempt
def scan_tables(request):
    """ HTML string is sent from extension to backend """

    received_data = json.loads(request.body)

    url_from_frontend = received_data["page_url"]
    print('URL from Frontend:  ', url_from_frontend)
    html_from_frontend = received_data["page_html"]

    is_localhost = "127.0.0.1:8000" in request.build_absolute_uri()

    download_links_, caught_table_indices = scrape_tables(html_from_frontend, is_localhost)

    data = {
        'connection': 'Successful',
        'input': url_from_frontend,
        'download_links': download_links_,
        'table_indices': caught_table_indices
    }
    print('Json Data to be sent: ', data)
    return JsonResponse(data)


def scrape_tables(html, is_localhost):
    try:

        # create a dummy table before each table so that later we can identify which tables were recognized by pandas
        slices = html.split("<table")
        table_count = 0
        new_tables = []
        for a_slice in slices:
            if "</table>" in a_slice:
                dummy_table = "<table><tr><td>table_id_" + str(table_count) + "</td></tr></table>"
                table_count += 1
                new_table = dummy_table + "<table" + a_slice
                new_tables.append(new_table)
        html = slices[0] + "".join(new_tables)

        #

        ssl._create_default_https_context = ssl._create_unverified_context
        scraper = pd.read_html(html)

        caught_table_indices = []  # identify which tables were recognized by pandas, we will send this info to content_script.js
        caught_table_index = 0  # index in the tables list at frontend
        data_table_count = 0
        download_links = []
        for i in range(0, len(scraper)):

            dimensions = scraper[i].to_numpy().shape
            if dimensions[0] == 0 or dimensions[1] == 0:
                continue

            is_this_table_id = str(scraper[i].to_numpy()[0][0])
            if "table_id_" in is_this_table_id:
                # a dummy table we created
                caught_table_index = int(is_this_table_id.replace("table_id_", ""))

            else:  # an actual data table
                caught_table_indices.append(caught_table_index)
                data_table_count += 1

                cleanup_table(scraper[i])

                # save each table .csv
                if is_localhost:
                    scraper[i].to_csv("backend/static/fetched_tables/table_" + str(data_table_count) + ".csv", encoding='utf-8', index=False)
                    download_links.append("http://127.0.0.1:8000/static/fetched_tables/table_" + str(data_table_count) + ".csv")
                    # example static link to get tables: http://127.0.0.1:8000/static/fetched_tables/table_1.csv
                else:
                    scraper[i].to_csv(str(os.path.join(BASE_DIR, 'static/fetched_tables/table_')) + str(data_table_count) + ".csv", encoding='utf-8', index=False)
                    download_links.append("https://tablecatcher.azurewebsites.net/static/fetched_tables/table_" + str(data_table_count) + ".csv")

        return download_links, caught_table_indices

    except ValueError:
        print("No Table Found on this website.")
        return [], []


def cleanup_table(table):

    # Delete columns with all NaN values
    table.dropna(axis=1, how="all", inplace=True)
    # Delete rows with more than half NaN values
    table.dropna(axis=0, thresh=int(table.shape[1] / 2), inplace=True)

    # remove columns named "Unnamed: ..."
    table.drop(list(table.filter(regex='Unnamed:')), axis=1, inplace=True)


@csrf_exempt
def table_from_screenshot(request):

    received_data = json.loads(request.body)
    print('Screenshot from frontend.')

    is_localhost = "127.0.0.1:8000" in request.build_absolute_uri()

    download_links_ = catch_tables_from_screenshot(received_data["screenshot"], is_localhost)

    data = {
        'download_links': download_links_,
    }
    print('Json Data to be sent: ', data)
    return JsonResponse(data)


def catch_tables_from_screenshot(base64_image_string, is_localhost):

    download_links_ = []
    saving_directory = str(os.path.join(BASE_DIR, 'static/screenshot_tables/'))
    download_directory = "https://tablecatcher.azurewebsites.net/static/screenshot_tables/"
    if is_localhost:
        saving_directory = "backend/static/screenshot_tables/"
        download_directory = "http://127.0.0.1:8000/static/screenshot_tables/"

    # create image file
    img_data = base64.b64decode(base64_image_string.split(",")[1])  # because starts like "data:image/png;base64,iVB..."
    img_file = open(saving_directory + 'screenshot_image' + '.png', 'wb')
    img_file.write(img_data)
    img_file.close()

    ocr = AzureOCR(endpoint="https://delavision.cognitiveservices.azure.com/", subscription_key="6e9b93fe9de5428b9fbfd63dd1349f91")

    image = Image(saving_directory + "screenshot_image.png")
    start = time.time()

    try:

        extracted_tables = image.extract_tables(ocr=ocr, implicit_rows=True, borderless_tables=True, min_confidence=5)
        if extracted_tables:  # if not empty list
            # without the if, creates an empty Excel file
            # one worksheet (excel page) per table, in single file
            image.to_xlsx(dest=saving_directory + "table.xlsx", ocr=ocr, implicit_rows=True, borderless_tables=True, min_confidence=5)
            download_links_.append(download_directory + "table.xlsx")

            # one csv file per table. (screenshot might include or interpreted as including multiple tables).
            for n, extracted_table in enumerate(extracted_tables):
                extracted_table.df.to_csv(saving_directory + "table_" + str(n+1) + ".csv", encoding='utf-8', index=False)
                download_links_.append(download_directory + "table_" + str(n+1) + ".csv")

        os.remove(saving_directory + "screenshot_image.png")
        print("* * * took ", str(int(time.time() - start)), " seconds. success * * * ")
        return download_links_

    except Exception:
        # print(traceback.format_exc())
        print("* * * took ", str(int(time.time() - start)), " seconds. NO Table ! * * * ")
        return []
