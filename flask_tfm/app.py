from gevent import monkey; monkey.patch_all()
from flask import Flask
from flask import render_template
import time
import requests
import json
from flask import request, url_for, redirect, session
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly
import lightgbm as lgb
import pandas as pd

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

@app.route("/tfm/<gameid>/<minute>",  methods=["POST", "GET"])
def tfm_visual(gameid,minute):
    if request.method == "POST":

        id = request.form.get("gameid")
        api_key = "RGAPI-a8585106-4f99-4026-aa58-278a3c468d06"
        df = pd.read_pickle("finalinfo.pkl")
        y = df["BlueWin"]

        data = {}
        kills = 0;
        ekills = 0
        gold = 0;
        egold = 0
        xp = 0;
        exp = 0
        cs = 0;
        ecs = 0
        drakes = 0;
        edrakes = 0
        heralds = 0;
        eheralds = 0
        towers = 0;
        etowers = 0
        plates = 0;
        eplates = 0
        dmg = 0;
        edmg = 0
        wards = 0;
        ewards = 0

        response = requests.get("https://europe.api.riotgames.com/lol/match/v5/matches/" + id + "/timeline?api_key=" + api_key + "").json()
        # First 15min loop
        for j in range(1, 16):

            # Events loop
            for k in range(0, len(response["info"]["frames"][j]["events"])):

                # KillsDiff
                if response["info"]["frames"][j]["events"][k]["type"] == "CHAMPION_KILL":
                    if response["info"]["frames"][j]["events"][k]["killerId"] <= 5:
                        kills += 1
                    else:
                        ekills += 1

                        # DrakesDiff & HeraldsDiff
                if response["info"]["frames"][j]["events"][k]["type"] == "ELITE_MONSTER_KILL":
                    if response["info"]["frames"][j]["events"][k]["monsterType"] == "DRAGON":
                        if response["info"]["frames"][j]["events"][k]["killerId"] <= 5:
                            drakes += 1
                        else:
                            edrakes += 1

                    elif response["info"]["frames"][j]["events"][k]["monsterType"] == "RIFTHERALD":
                        if response["info"]["frames"][j]["events"][k]["killerId"] <= 5:
                            heralds += 1
                        else:
                            eheralds += 1

                # TowersDiff
                if response["info"]["frames"][j]["events"][k]["type"] == "BUILDING_KILL":
                    if response["info"]["frames"][j]["events"][k]["buildingType"] == "TOWER_BUILDING":
                        if response["info"]["frames"][j]["events"][k]["teamId"] == 200:
                            towers += 1
                        else:
                            etowers += 1

                # PlatesDiff
                if response["info"]["frames"][j]["events"][k]["type"] == "TURRET_PLATE_DESTROYED":
                    if response["info"]["frames"][j]["events"][k]["teamId"] == 200:
                        plates += 1
                    else:
                        eplates += 1

                # WardsDiff
                if response["info"]["frames"][j]["events"][k]["type"] == "WARD_PLACED":
                    if response["info"]["frames"][j]["events"][k]["creatorId"] <= 5:
                        wards += 1
                    else:
                        ewards += 1

            # Players Loop
            for k in range(1, 11):

                # GoldDiff
                if k <= 5:
                    gold += response["info"]["frames"][j]["participantFrames"][str(k)]["totalGold"]
                else:
                    egold += response["info"]["frames"][j]["participantFrames"][str(k)]["totalGold"]

                # XpDiff
                if k <= 5:
                    xp += response["info"]["frames"][j]["participantFrames"][str(k)]["xp"]
                else:
                    exp += response["info"]["frames"][j]["participantFrames"][str(k)]["xp"]

                    # CsDiff
                if k <= 5:
                    cs += response["info"]["frames"][j]["participantFrames"][str(k)]["minionsKilled"] + \
                          response["info"]["frames"][j]["participantFrames"][str(k)]["jungleMinionsKilled"]
                else:
                    ecs += response["info"]["frames"][j]["participantFrames"][str(k)]["minionsKilled"] + \
                           response["info"]["frames"][j]["participantFrames"][str(k)]["jungleMinionsKilled"]

                # DmgDiff
                if k <= 5:
                    dmg += response["info"]["frames"][j]["participantFrames"][str(k)]["damageStats"][
                        "totalDamageDoneToChampions"]
                else:
                    edmg += response["info"]["frames"][j]["participantFrames"][str(k)]["damageStats"][
                        "totalDamageDoneToChampions"]

            # Final append to dict
            data["kd" + str(j) + ""] = [kills - ekills]
            data["gd" + str(j) + ""] = [gold - egold]
            data["xpd" + str(j) + ""] = [xp - exp]
            data["csd" + str(j) + ""] = [cs - ecs]
            data["dd" + str(j) + ""] = [drakes - edrakes]
            data["hd" + str(j) + ""] = [heralds - eheralds]
            data["td" + str(j) + ""] = [towers - etowers]
            data["pd" + str(j) + ""] = [plates - eplates]
            data["tdd" + str(j) + ""] = [dmg - edmg]
            data["wd" + str(j) + ""] = [wards - ewards]

            kills = 0;
            ekills = 0
            gold = 0;
            egold = 0
            xp = 0;
            exp = 0
            cs = 0;
            ecs = 0
            drakes = 0;
            edrakes = 0
            heralds = 0;
            eheralds = 0
            towers = 0;
            etowers = 0
            plates = 0;
            eplates = 0
            dmg = 0;
            edmg = 0
            wards = 0;
            ewards = 0

        for k in range(0, len(response["info"]["frames"][len(response["info"]["frames"]) - 1]["events"])):
            if response["info"]["frames"][len(response["info"]["frames"]) - 1]["events"][k]["type"] == "GAME_END":
                if response["info"]["frames"][len(response["info"]["frames"]) - 1]["events"][k]["winningTeam"] == 100:
                    data["BlueWin"] = True
                else:
                    data["BlueWin"] = False

        data["gameId"] = [gameid]

        df_temp = pd.DataFrame(data)
        df_temp.set_index('gameId')

        print("df terminado")

        lgbm_model = lgb.LGBMClassifier(boosting_type='gbdt', num_leaves=50, max_depth=5, is_unbalance=False)
        imagenes = []
        mensaje = []
        plot_bgcolor = "#23272A"
        quadrant_colors = [plot_bgcolor, "#2bad4e","#85e043",  "#eff229" , "#f2a529","#f25829"]
        quadrant_text = ["", "<b>Very High</b>", "<b>High</b>", "<b>Medium</b>", "<b>Low</b>", "<b>Very Low</b>"]
        n_quadrants = len(quadrant_colors) - 1

        for i in range(15):
            X = df[["kd" + str(i + 1) + "", "gd" + str(i + 1) + "", "xpd" + str(i + 1) + "", "csd" + str(i + 1) + "",
                    "dd" + str(i + 1) + "", "hd" + str(i + 1) + "", "td" + str(i + 1) + "", "pd" + str(i + 1) + "",
                    "tdd" + str(i + 1) + "", "wd" + str(i + 1) + ""]]
            X["gd" + str(i + 1)] = X["gd" + str(i + 1)].astype('int32')
            lgbm_model.fit(X, y)
            Xnew = df_temp[
                ["kd" + str(i + 1) + "", "gd" + str(i + 1) + "", "xpd" + str(i + 1) + "", "csd" + str(i + 1) + "",
                 "dd" + str(i + 1) + "", "hd" + str(i + 1) + "", "td" + str(i + 1) + "", "pd" + str(i + 1) + "",
                 "tdd" + str(i + 1) + "", "wd" + str(i + 1) + ""]]
            Xnew["gd" + str(i + 1)] = Xnew["gd" + str(i + 1)].astype('int32')

            if i > 0:
                Xold = df_temp[
                    ["kd" + str(i) + "", "gd" + str(i) + "", "xpd" + str(i) + "", "csd" + str(i) + "","dd" + str(i) + "", "hd" + str(i) + "", "td" + str(i) + "", "pd" + str(i) + "",
                     "tdd" + str(i) + "", "wd" + str(i) + ""]]
                Xold["gd" + str(i)] = Xold["gd" + str(i)].astype('int32')

                if Xold["dd" + str(i)+ ""].item() < Xnew["dd" + str(i+1)+ ""].item():
                    mensaje.append("Minuto "+str(i+1)+" drake del Blue Team  ")
                if Xold["hd" + str(i)+ ""].item() < Xnew["hd" + str(i+1)+ ""].item():
                    mensaje.append("Minuto "+str(i+1)+" herald del Blue Team  ")
                if Xold["td" + str(i)+ ""].item() < Xnew["td" + str(i+1)+ ""].item():
                    mensaje.append("Minuto "+str(i+1)+" torre del Blue Team  ")
                if Xold["pd" + str(i)+ ""].item() < Xnew["pd" + str(i+1)+ ""].item():
                    mensaje.append("Minuto "+str(i+1)+" placa de torre del Blue Team  ")

                if Xold["dd" + str(i)+ ""].item() > Xnew["dd" + str(i+1)+ ""].item():
                    mensaje.append("Minuto "+str(i+1)+" drake del Red Team  ")
                if Xold["hd" + str(i)+ ""].item() > Xnew["hd" + str(i+1)+ ""].item():
                    mensaje.append("Minuto "+str(i+1)+" herald del Red Team  ")
                if Xold["td" + str(i)+ ""].item() > Xnew["td" + str(i+1)+ ""].item():
                    mensaje.append("Minuto "+str(i+1)+" torre del Red Team  ")
                if Xold["pd" + str(i)+ ""].item() > Xnew["pd" + str(i+1)+ ""].item():
                    mensaje.append("Minuto "+str(i+1)+" placa de torre del Red Team  ")

            current_value = round(lgbm_model.predict_proba(Xnew)[0][1]*100,2)
            min_value = 0
            max_value = 100
            hand_length = np.sqrt(2) / 4
            hand_angle = np.pi * (1 - (max(min_value, min(max_value, current_value)) - min_value) / (max_value - min_value))

            fig = go.Figure(
                data=[
                    go.Pie(
                        values=[0.5] + (np.ones(n_quadrants) / 2 / n_quadrants).tolist(),
                        rotation=90,
                        hole=0.5,
                        marker_colors=quadrant_colors,
                        text=quadrant_text,
                        textinfo="text",
                        hoverinfo="skip",
                    ),
                ],
                layout=go.Layout(
                    showlegend=False,
                    margin=dict(b=0, t=10, l=10, r=10),
                    width=450,
                    height=450,
                    paper_bgcolor=plot_bgcolor,
                    annotations=[
                        go.layout.Annotation(
                            text=f"<b>{current_value}% al minuto: "+str(i+1)+"</b><br>",
                            x=0.5, xanchor="center", xref="paper",
                            y=0.25, yanchor="bottom", yref="paper",
                            showarrow=False,
                        )
                    ],
                    shapes=[
                        go.layout.Shape(
                            type="circle",
                            x0=0.48, x1=0.52,
                            y0=0.48, y1=0.52,
                            fillcolor="#1870d5",
                            line_color="#1870d5",
                        ),
                        go.layout.Shape(
                            type="line",
                            x0=0.5, x1=0.5 + hand_length * np.cos(hand_angle),
                            y0=0.5, y1=0.5 + hand_length * np.sin(hand_angle),
                            line=dict(color="#1870d5", width=4)
                        )
                    ]
                )
            )
            print("imagen "+str(i))
            fig.update_annotations(font_color= "#FFFFFF")
            imagenes.append(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))


        return render_template('tfm2.html', imagenes = imagenes,mensaje=mensaje)
    else:
        return render_template('tfm.html')
