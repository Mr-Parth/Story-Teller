import pandas as Panda
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit, send
import json
import time
import numpy as np
from nlp import analyze, suggest

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'


socketio = SocketIO(app, binary=True)

file = Panda.read_csv("hack.csv", skiprows=0)

file.replace("Not available", 0, inplace=True)
file.replace("Not Available", 0, inplace=True)
file.fillna(0, axis=0, inplace=True)

file = file[file["Tier"] == "Total"]

columns = list(file.columns)


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def missing(d):
    print(d)
    d = Panda.to_numeric(d)
    if type(d) == type(0.0) or str(d).isdigit() or isfloat(str(d)):
        print("1")
        return str(d)
    if sum(d) != 0:
        d[np.isnan(d)] = 0
        print("2")
        return d.tolist()
    else:
        print("3")
        return ["-1"]


def check_case(data):
    return [i for i in range(len(columns)) if columns[i].lower() == data.lower()][0]


def operator_resolve(a, op, b):
    par = {"Add": a+b, "Sub": a-b, "Mul": a*b, "Div": a //
           b, "gt": a > b, "lt": a < b, "eq": a == b}
    try:
        return par[op]
    except:
        return "0"


@socketio.on('connect')
def connect():
    print("connect")
    emit("reciever", [[10, 20, 10], ["a", "b", "c"], "dummy"])
    time.sleep(1)


@socketio.on('channel')
def channel(data):
    try:
        print(data)
        sugg = []

        if type(data) == type("test"):
            cat, val, col, name, op, col2 = analyze(data)
            sugg = suggest(data)
            print(sugg)

        else:
            if len(data) == 3:
                data.extend(["", "", ""])

            cat, val, col, name, op, col2 = data

        print([cat, val, col, name, op, col2])
        lab = "District" if cat == "State" else "State" if cat == "Nation" else "Tier"
        print(val)

        if col2 == "":
            if col == "none":
                pass
            else:
                chk = ["%", "Mean", "per"]
                if cat == "Nation":
                    l = ["%", "Mean", "per"]
                    if max([col.find(i) for i in l]) >= 0:
                        emit('reciever', [missing(
                            file[["State", col]].groupby("State").agg(
                                lambda x:x.value_counts().index[0])[col].tolist()),
                            file.groupby("State").sum().index.tolist(),
                            "Most Common " + col + " in every state  |  " + cat.upper() + "  |   " +
                            val.upper(), data, sugg
                        ])
                    else:
                        emit('reciever', [
                            missing(file.groupby("State").sum()
                                    [col].tolist()),
                            file.groupby("State").sum().index.tolist(),
                            "Cummulative " + col + " in every state  |  " + cat.upper() + "  |   "+val.upper(), data, sugg])

                else:
                    dt2 = file.set_index(cat).loc[val]
                    print(np.array(dt2[col]).tolist())
                    emit('reciever', [
                        missing(np.array(dt2[col]).tolist()),
                        np.array(dt2[lab]).tolist(),
                        col+"  |  " + cat.upper() + "  |   "+val.upper(), data, sugg])
                time.sleep(0.5)
        if col2 != "" and op != "":
            name = name if name != "" else "Unname"
            if op not in ["Correlation", "gt", "lt", "eq"]:
                file[name] = operator_resolve(Panda.to_numeric(
                    file[col], errors='coerce'), op, Panda.to_numeric(file[col2], errors='coerce'))
                col = name
                if col == "none":
                    pass
                else:
                    chk = ["%", "Mean", "per"]
                    if cat == "Nation":
                        l = ["%", "Mean", "per"]
                        if max([col.find(i) for i in l]) >= 0:
                            emit('reciever', [missing(
                                file[["State", col]].groupby("State").agg(
                                    lambda x:x.value_counts().index[0])[col].tolist()),
                                file.groupby("State").sum().index.tolist(),
                                "Most Common " + col + " in every state  |  " + cat.upper() + "  |   "+val.upper(), data, sugg])
                        else:
                            emit('reciever', [
                                missing(file.groupby("State").sum()
                                        [col].tolist()),
                                file.groupby("State").sum().index.tolist(),
                                "Cummulative " + col + " in every state  |  " + cat.upper() + "  |   "+val.upper(), data, sugg])

                    else:
                        dt2 = file.set_index(cat).loc[val]
                        print(np.array(dt2[col]).tolist())
                        emit('reciever', [
                            missing(np.array(dt2[col]).tolist()),
                            np.array(dt2[lab]).tolist(),
                            col+"  |  " + cat.upper() + "  |   "+val.upper(), data, sugg])
                    time.sleep(0.5)
            elif op == "Correlation" and cat != "District":
                dt2 = file.set_index(cat).loc[val]
                cor = str(dt2[col].astype("float32").corr(
                    dt2[col2].astype("float32")))
                emit('reciever', [
                    cor[:7] if cor != "nan" else "0",
                    "",
                    col+"  |  " + cat.upper() + "  |   "+val.upper(), data, sugg])
            elif op in ["gt", "lt", "eq"] and cat != "District":
                if cat == "Nation":
                    dt2 = file
                else:
                    dt2 = file.set_index(cat).loc[val]
                dt2 = dt2[operator_resolve(dt2[col].astype(
                    "float32"), op, dt2[col2].astype("float32"))]
                emit('reciever', [
                    list(set(np.array(dt2[lab]).tolist())),
                    list(set(np.array(dt2[lab]).tolist())),
                    col+"  |  " + cat.upper() + "  |   "+val.upper(), data, sugg])

            else:
                print("error")
                pass
    except:
        emit('reciever', [
            "Bad Data",
            "",
            ""])


@app.route('/index')
def hello_world():
    col = columns
    state = list(file['State'].drop_duplicates().sort_index())
    district = list(file['District'].drop_duplicates().sort_index())

    return render_template('index.html', catagory=[col[4:], state, district])


if __name__ == '__main__':
    socketio.run(app)
