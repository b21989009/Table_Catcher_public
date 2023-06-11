from django.http import JsonResponse
from django.shortcuts import render
import pandas as pd
import ssl
import json
import os
import base64
import shutil
from dataclasses import dataclass
from typing import Optional, NamedTuple
from collections import OrderedDict
import time
from zipfile import ZipFile
from os.path import basename
import traceback

# https://github.com/xavctn/img2table
from img2table.document import Image
from img2table.ocr import AzureOCR

from django.views.decorators.csrf import csrf_exempt
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


""" DOCUMENTATION WEBSITE"""


def main(request):
    return render(request, 'main.html')


def team(request):
    return render(request, 'team.html')


def guide(request):
    return render(request, 'guide.html')


def project(request):
    return render(request, 'project.html')


def video(request):
    return render(request, 'video.html')


""" TABLE CATCHER FUNCTIONS"""


def test_connection(request):
    print(request)

    # clean-up the server if static folders are filled with too many tables.

    static_directory = "backend/static/"
    is_localhost = "127.0.0.1:8000" in request.build_absolute_uri()
    if not is_localhost:  # Azure
        static_directory = str(os.path.join(BASE_DIR, 'backend/static/'))
    scanned_subfolder_count = sum(1 for entry in os.scandir(static_directory + "scanned_tables/"))
    screenshot_subfolder_count = sum(1 for entry in os.scandir(static_directory + "screenshot_tables/"))
    # print("\n\n COUNT:  ", scanned_subfolder_count, " - ", screenshot_subfolder_count, " ** * * \n")
    if scanned_subfolder_count > 500:
        start = time.time()
        shutil.rmtree(static_directory + "scanned_tables/", ignore_errors=True)  # delete folder
        os.mkdir(static_directory + "scanned_tables/")  # recreate folder
        print("\n * * * CLEANED UP  /SCANNED_TABLES/  FOLDER   in  ", int(time.time() - start), "  seconds.  * * *\n")
    if screenshot_subfolder_count > 500:
        start = time.time()
        shutil.rmtree(static_directory + "screenshot_tables/", ignore_errors=True)  # delete folder
        os.mkdir(static_directory + "screenshot_tables/")  # recreate folder
        print("\n * * * CLEANED UP  /SCREENSHOT_TABLES/  FOLDER   in  ", int(time.time() - start), "  seconds.  * * *\n")

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

    session_id = received_data["session_id"]
    print("session_id:  ", session_id)

    url_from_frontend = received_data["page_url"]
    print('URL from Frontend:  ', url_from_frontend)
    html_from_frontend = received_data["page_html"]

    is_localhost = "127.0.0.1:8000" in request.build_absolute_uri()

    # time.sleep(5)  # testing the loading spinner in extension popup

    csv_download_links_, excel_download_links_, caught_table_indices, zip_download_link_ = scrape_tables(html_from_frontend, is_localhost, session_id)

    data = {
        'connection': 'Successful',
        'input': url_from_frontend,
        'csv_download_links': csv_download_links_,
        'excel_download_links': excel_download_links_,
        'zip_download_link': zip_download_link_,
        'table_indices': caught_table_indices
    }
    print('Json Data to be sent: ', data)
    return JsonResponse(data)


def scrape_tables(html, is_localhost, session_id):

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

        # before: <class 'str'>    after:  <class 'bytes'>
        html = html.encode(encoding="utf-8", errors='strict')

        # security
        ssl._create_default_https_context = ssl._create_unverified_context
        
        """ Extract tables from HTML """
        scraper = pd.read_html(html)

        caught_table_indices = []  # identify which tables were recognized by Pandas. we will send this info to content_script.js
        caught_table_index = 0  # index in the list of tables at frontend
        data_table_count = 0
        csv_download_links = []
        excel_download_links = []

        saving_directory = ""
        download_directory = ""
        zip_download_link = ""
        zip_path = ""
        if is_localhost:
            zip_path = 'backend/static/scanned_tables/' + session_id + '/tables.zip'
            zip_download_link = "http://127.0.0.1:8000/static/scanned_tables/" + session_id + "/tables.zip"

            saving_directory = "backend/static/scanned_tables/" + session_id + "/"
            download_directory = "http://127.0.0.1:8000/static/scanned_tables/" + session_id + "/"

        else:  # Azure
            zip_path = str(os.path.join(BASE_DIR, 'backend/static/scanned_tables/' + session_id + '/tables.zip'))
            zip_download_link = "https://tablecatcher.azurewebsites.net/static/scanned_tables/" + session_id + "/tables.zip"

            saving_directory = str(os.path.join(BASE_DIR, 'backend/static/scanned_tables/' + session_id + '/'))
            download_directory = "https://tablecatcher.azurewebsites.net/static/scanned_tables/" + session_id + "/"

        # create a new folder with session id
        if os.path.exists(saving_directory):
            shutil.rmtree(saving_directory, ignore_errors=True)  # delete folder
        os.mkdir(saving_directory)
        zip_download_all = ZipFile(zip_path, 'w')

        for i in range(0, len(scraper)):  # each Table candidate

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

                header_is_useful = cleanup_table(scraper[i])

                # Save CSV
                file_path_ = saving_directory + "table_" + str(data_table_count) + ".csv"
                scraper[i].to_csv(file_path_, encoding='utf-8', index=False, header=header_is_useful)
                zip_download_all.write(file_path_, basename(file_path_))
                csv_download_links.append(download_directory + "table_" + str(data_table_count) + ".csv")

                # Save EXCEL
                excel_ = "table_" + str(data_table_count) + ".xlsx"
                file_path_ = saving_directory + excel_
                format_excel_for_scan_method(scraper[i], file_path_, excel_, zip_download_all, excel_download_links, download_directory, header_is_useful)

        zip_download_all.close()
        return csv_download_links, excel_download_links, caught_table_indices, zip_download_link

    except ValueError:
        print("No Table Found on this Page.")
        return [], [], [], ""

    except:
        print(traceback.format_exc())
        return [], [], [], ""


def cleanup_table(table):

    # Delete columns with all NaN values
    table.dropna(axis=1, how="all", inplace=True)
    
    # Delete rows with all NaN values
    if table.shape[1] < 2:  # table is just a list
        table.dropna(axis=0, thresh=1, inplace=True)
    else:
        table.dropna(axis=0, thresh=2, inplace=True)

    # remove columns named "Unnamed: ..."
    table.drop(list(table.filter(regex='Unnamed:')), axis=1, inplace=True)

    # wikipedia specific: delete first row or header if it is css meta-data
    if "mw-parser-output" in str(table.columns):
        return False
    else:
        return True


@csrf_exempt
def table_from_screenshot(request):

    received_data = json.loads(request.body)
    print('Screenshot from frontend.')

    session_id = received_data["session_id"]
    print("session_id:  ", session_id)

    is_localhost = "127.0.0.1:8000" in request.build_absolute_uri()

    download_links_ = catch_tables_from_screenshot(received_data["screenshot"], is_localhost, session_id)

    data = {
        'download_links': download_links_,
    }
    print('Json Data to be sent: ', data)
    return JsonResponse(data)


# taken from the source code of the img2table library
@dataclass
class TableCell:
    x1: int
    y1: int
    x2: int
    y2: int
    value: Optional[str]

    def __hash__(self):
        return hash(repr(self))


def catch_tables_from_screenshot(base64_image_string, is_localhost, session_id):

    download_links_ = []
    saving_directory = ""
    download_directory = ""
    if is_localhost:
        saving_directory = "backend/static/screenshot_tables/" + session_id + "/"
        download_directory = "http://127.0.0.1:8000/static/screenshot_tables/" + session_id + "/"
    else:
        saving_directory = str(os.path.join(BASE_DIR, 'backend/static/screenshot_tables/')) + session_id + "/"
        download_directory = "https://tablecatcher.azurewebsites.net/static/screenshot_tables/" + session_id + "/"

    # create a new folder with session id
    if os.path.exists(saving_directory):
        shutil.rmtree(saving_directory, ignore_errors=True)  # delete folder
    os.mkdir(saving_directory)

    # create image file
    img_data = base64.b64decode(base64_image_string.split(",")[1])  # because starts like "data:image/png;base64,iVB..."
    img_file = open(saving_directory + 'screenshot_image.png', 'wb')
    img_file.write(img_data)
    img_file.close()

    ocr = AzureOCR(endpoint="https://delavision.cognitiveservices.azure.com/", subscription_key="6e9b93fe9de5428b9fbfd63dd1349f91")

    image = Image(saving_directory + "screenshot_image.png")
    start = time.time()

    try:
        extracted_tables = image.extract_tables(ocr=ocr, implicit_rows=True, borderless_tables=True, min_confidence=5)

        if extracted_tables:  # if not empty list

            # Concatenate tables (which are adjacent in the list) pair-wise in-place,
            # if the same number of columns (because sometimes recognized as separate tables).
            if len(extracted_tables) > 1:
                start_index = 0
                print("shapes of all tables:  ", end=" ")
                for t in extracted_tables:
                    print(t.df.shape, end=" ")
                print()
                while start_index < len(extracted_tables) - 1:
                    table_1_ = extracted_tables[start_index]
                    table_2_ = extracted_tables[start_index + 1]
                    dataframe_1 = table_1_.df
                    dataframe_2 = table_2_.df

                    if len(dataframe_1.columns) == len(dataframe_2.columns):
                        table_1_rowcount = dataframe_1.shape[0]

                        # insert empty row in between
                        table_1_.content[table_1_rowcount] = [TableCell(x1=9999, x2=9999, y1=9999, y2=9999, value=" ") for _ in range(dataframe_1.shape[1])]
                        table_1_.content[table_1_rowcount + 1] = [TableCell(x1=9999, x2=9999, y1=9999, y2=9999, value=" ") for _ in range(dataframe_1.shape[1])]

                        # Concatenate tables by transferring rows
                        for i in range(dataframe_2.shape[0]):
                            table_1_.content[table_1_rowcount + i + 2] = table_2_.content[i]  # a List[TableCell]

                        # table_2 is concatenated to the end of table_1 object. Thus remove table_2 from the list
                        extracted_tables.pop(start_index + 1)
                        print(" CONCATENATED ")
                    else:
                        start_index += 1

            # CSV
            # one csv file per table. (screenshot might include or be interpreted as including multiple tables).
            for n, extracted_table in enumerate(extracted_tables):
                extracted_table = extracted_table.df
                extracted_table.to_csv(saving_directory + "table_" + str(n+1) + ".csv", encoding='utf-8', header=False, index=False)
                download_links_.append(download_directory + "table_" + str(n+1) + ".csv")

            # EXCEL
            # one worksheet (excel page) per table, in single file
            format_excel_for_screenshot_method(extracted_tables, download_links_, download_directory, file_path_=saving_directory + "table.xlsx")

            print("* * * took ", str(int(time.time() - start)), " seconds. success * * * ")

        else:
            print("* * * took ", str(int(time.time() - start)), " seconds. NO Table ! * * * ")

        os.remove(saving_directory + "screenshot_image.png")
        return download_links_

    except:
        print(traceback.format_exc())
        print("* * * took ", str(int(time.time() - start)), " seconds. NO Table ! * * * ")
        return []


def format_excel_for_screenshot_method(extracted_tables, download_links_, download_directory, file_path_):

    class CellPosition(NamedTuple):
        cell: TableCell
        row: int
        col: int

    with pd.ExcelWriter(file_path_, engine='xlsxwriter') as writer:

        for n, extracted_table in enumerate(extracted_tables):
            can_continue = True

            extracted_table_data_frame = extracted_table.df
            try:
                extracted_table_data_frame.to_excel(writer, sheet_name='Table ' + str(n + 1), header=False, index=False)
            except NotImplementedError:
                try:
                    extracted_table_data_frame.to_excel(writer, sheet_name='Table ' + str(n + 1), header=False, index=True)
                except:
                    can_continue = False

            if can_continue:

                download_links_.append(download_directory + "table.xlsx")
                download_links_ = list(OrderedDict.fromkeys(download_links_))  # remove duplicates

                workbook = writer.book
                sheet = workbook.get_worksheet_by_name('Table ' + str(n + 1))

                """ MERGE MERGED CELLS """
                # below is taken from the image.to_xlsx() source code of the img2table library
                # Group cells based on hash (merged cells are duplicated over multiple rows/columns in content)
                dict_cells = dict()
                for id_row, row in extracted_table.content.items():
                    for id_col, cell in enumerate(row):
                        dict_cells[hash(cell)] = dict_cells.get(hash(cell), []) + [CellPosition(cell=cell, row=id_row, col=id_col)]

                for c in dict_cells.values():
                    if len(c) != 1:  # merged cells
                        sheet.merge_range(first_row=min(map(lambda x: x.row, c)),
                                          first_col=min(map(lambda x: x.col, c)),
                                          last_row=max(map(lambda x: x.row, c)),
                                          last_col=max(map(lambda x: x.col, c)),
                                          data=c[0].cell.value)

                """ Formatting cells to be readable and automatic width """
                cell_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'border': 1})
                bold_header = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'bold': True})

                table_range = 'A1:' + chr(ord('A') + extracted_table_data_frame.shape[1] - 1) + str(extracted_table_data_frame.shape[0])
                sheet.conditional_format(table_range, {'type': 'no_blanks', 'format': cell_format})
                sheet.conditional_format(table_range, {'type': 'blanks', 'format': cell_format})

                first_row = 'A1:' + chr(ord('A') + extracted_table_data_frame.shape[1] - 1) + '1'
                sheet.conditional_format(first_row, {'type': 'no_blanks', 'format': bold_header})
                sheet.conditional_format(first_row, {'type': 'blanks', 'format': bold_header})

                # sheet.set_column(0, extracted_table_data_frame.shape[1] - 1, None, cell_format) # all cells of all columns
                # sheet.set_row(0, None, bold_header)

                sheet.autofit()


def format_excel_for_scan_method(table, file_path_, excel_, zip_file, excel_download_links, download_directory, header_is_useful):

    try:
        with pd.ExcelWriter(file_path_, engine='xlsxwriter') as writer:

            can_continue = True
            try:
                table.to_excel(writer, sheet_name='Table', index=False, header=header_is_useful)
            except NotImplementedError:
                try:
                    table.to_excel(writer, sheet_name='Table', index=True, header=header_is_useful)
                except:
                    can_continue = False

            if can_continue:
                """ Formatting cells to be readable and automatic width """

                workbook = writer.book
                sheet = workbook.get_worksheet_by_name('Table')

                # Auto width for columns (fit the content)
                # taken from: https://towardsdatascience.com/how-to-auto-adjust-the-width-of-excel-columns-with-pandas-excelwriter-60cee36e175e
                for column in table:
                    column_width = 0
                    if header_is_useful:
                        column_width = max(table[column].astype(str).map(len).max(), len(str(column)))
                    else:
                        column_width = table[column].astype(str).map(len).max()
                    col_idx = table.columns.get_loc(column)
                    sheet.set_column(col_idx, col_idx, column_width)

                cell_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'border': 1})
                bold_header = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'bold': True})

                table_range = 'A2:' + chr(ord('A') + table.shape[1] - 1) + str(table.shape[0] + 1)
                sheet.conditional_format(table_range, {'type': 'no_blanks', 'format': cell_format})
                sheet.conditional_format(table_range, {'type': 'blanks', 'format': cell_format})

                first_row = 'A1:' + chr(ord('A') + table.shape[1] - 1) + '1'
                sheet.conditional_format(first_row, {'type': 'no_blanks', 'format': bold_header})
                sheet.conditional_format(first_row, {'type': 'blanks', 'format': bold_header})

                sheet.autofit()

        zip_file.write(file_path_, basename(file_path_))
        excel_download_links.append(download_directory + excel_)

    except:
        print(traceback.format_exc())
