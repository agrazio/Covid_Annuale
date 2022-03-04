from urllib.request import urlopen
import json
import os
from datetime import datetime, date
from github import Github


def rolling_mean(data, window_size):
    i = 0
    moving_averages = []
    while i < len(data) - window_size + 1:
        this_window = data[i: i + window_size]
        window_average = sum(this_window) / window_size
        moving_averages.append(round(window_average))
        i += 1
    return moving_averages


def handler(request):
    url = os.environ.get('DATA_URL')
    git = Github(os.environ.get('GIT_KEY'))
    repo = git.get_repo(os.environ.get('GIT_REPO'))

    response = urlopen(url)
    data_json = json.loads(response.read())

    ricoverati_con_sintomi = [[], [], []]
    terapie_intensive = [[], [], []]
    totale_positivi = [[], [], []]
    nuovi_positivi = [[], [], []]
    date = [[], [], []]

    for value in data_json:
        data = datetime.fromisoformat(value["data"]).date()

        if data < datetime(2021, 2, 24).date():
            index = 0
        elif data >= datetime(2021, 2, 24).date() and data < datetime(2022, 2, 24).date():
            index = 1
        else:
            index = 2

        # modo poco elegante per superare l'anno bisestile
        if data != datetime(2020, 2, 29).date():
            ricoverati_con_sintomi[index].append(
                value["ricoverati_con_sintomi"])
        terapie_intensive[index].append(value["terapia_intensiva"])
        totale_positivi[index].append(value["totale_positivi"])
        nuovi_positivi[index].append(value["nuovi_positivi"])
        date[index].append(data.strftime("%Y-%m-%d"))

    nuovi_positivi = list(map(lambda x: rolling_mean(x, 7), nuovi_positivi))

    output = {}
    output["ricoverati_con_sintomi"] = ricoverati_con_sintomi
    output["terapie_intensive"] = terapie_intensive
    output["totale_positivi"] = totale_positivi
    output["nuovi_positivi"] = nuovi_positivi
    output["date"] = date
    new_data = json.dumps(output)
    content = repo.get_contents("output.json")
    repo.update_file(path=content.path, message="Auto update",
                     content=new_data, sha=content.sha, branch="master")

    return f'OK!'
