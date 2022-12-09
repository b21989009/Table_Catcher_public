from django.http import JsonResponse, HttpResponse
import pandas as pd
import ssl
from django.views.decorators.csrf import csrf_exempt


def index(request):
    print("Enes")
    data = {
        'no input': "DE LA WEBSITE index",
    }

    return JsonResponse(data)
    # return HttpResponse("DE LA WEBSITE")


def get_data(request):

    """http://127.0.0.1:8000/get/?topic=https://coinmarketcap.com/
    Böyle URL query parametresi değil, POST request içinde bir string gibi göndermeliyiz extension'dan backend'e.
    Aşağıdaki send_url fonksiyonu achieves this.
    """

    topic = request.GET.get('topic', None)
    print("Enes")
    print('Topic:', topic)

    data = {
        'Summary': 'SENT',
        'Raw': 'Successful',
        'input': topic,
        'table_data': scrape_table(topic)
    }

    print('Json Data to be sent: ', data)

    return JsonResponse(data)


@csrf_exempt
def send_url(request):

    url_from_frontend = ""

    if request.POST["tag"] == "whatever":
        url_from_frontend = request.POST["page_url"]

    print('URL from Frontend:  ', url_from_frontend)

    table_data_, download_links_ = scrape_table(url_from_frontend)

    data = {
        'connection': 'Successful',
        'input': url_from_frontend,
        'table_data': table_data_,
        'download_links': download_links_
    }

    print('Json Data to be sent: ', data)

    return JsonResponse(data)


def scrape_table(url):
    scraper = None
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        scraper = pd.read_html(url)

        table_string = []
        download_links = []

        for i in range(0, len(scraper)):

            cleanup_table(scraper[i])

            # save each table .csv
            scraper[i].to_csv("mysite/static/fetched_tables/table_" + str(i) + ".csv", encoding='utf-8', index=False)

            download_links.append("http://127.0.0.1:8000/static/fetched_tables/table_" + str(i) + ".csv")

            """ example STATIC LINKS TO GET TABLES:
            http://127.0.0.1:8000/static/fetched_tables/smile.jpg
            http://127.0.0.1:8000/static/fetched_tables/table_0.csv
            """

            # just to console.log to frontend
            table_string.append(scraper[i].to_numpy())
        # only to show it works, not all data
        return str(table_string)[0:40] + " ... ", download_links

    # no table on website
    except ValueError:
        print("No Table Found on this website.")
        return " ... ", []


def cleanup_table(table):

    # Delete columns with all NaN values
    table.dropna(axis=1, how="all", inplace=True)
    # Delete rows with more than half NaN values
    table.dropna(axis=0, thresh=int(table.shape[1] / 2), inplace=True)

    # remove columns named "Unnamed: ..."
    table.drop(list(table.filter(regex='Unnamed:')), axis=1, inplace=True)
