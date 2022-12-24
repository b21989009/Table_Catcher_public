from django.http import JsonResponse, HttpResponse
import pandas as pd
import ssl
import json
from django.views.decorators.csrf import csrf_exempt


def documentation(request):
    print(request)
    return HttpResponse("Table Catcher Documentation page. For testing if server works, for Documentation. ")


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
                scraper[i].to_csv("backend/static/fetched_tables/table_" + str(data_table_count) + ".csv", encoding='utf-8', index=False)

                # example static link to get tables: http://127.0.0.1:8000/static/fetched_tables/table_1.csv
                if is_localhost:
                    download_links.append("http://127.0.0.1:8000/static/fetched_tables/table_" + str(data_table_count) + ".csv")
                else:
                    download_links.append("https://table-catcher.herokuapp.com/static/fetched_tables/table_" + str(data_table_count) + ".csv")

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
