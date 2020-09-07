import pandas as pd
import numpy as np
import xgboost as xgb


def res(telemetry, errors, maint, failures, machines):

    telemetry["date_created"] = pd.to_datetime(telemetry["date_created"], format="%Y-%m-%d %H:%M:%S")

    errors["date_created"] = pd.to_datetime(errors["date_created"], format="%Y-%m-%d %H:%M:%S")
    errors["error"] = errors["error"].astype("category")

    maint["date_created"] = pd.to_datetime(maint["date_created"], format="%Y-%m-%d %H:%M:%S")
    maint["compID"] = maint["compID"].astype("category")

    machines["model"] = machines["model"].astype("category")

    failures["date_created"] = pd.to_datetime(failures["date_created"], format="%Y-%m-%d %H:%M:%S")
    failures["failure"] = failures["failure"].astype("category")


    temp = []
    fields = ["volt", "rotate", "pressure", "vibration"]

    temp = [
        pd.pivot_table(
            telemetry,
            index="date_created",
            columns="machine_id",
            values=col).resample("3H", closed="left", label="right").mean().unstack()
        for col in fields
    ]


    telemetry_mean_3h = pd.concat(temp, axis=1)
    telemetry_mean_3h.columns = [col + "mean_3h" for col in fields]
    telemetry_mean_3h.reset_index(inplace=True)


    temp = [
        pd.pivot_table(
            telemetry,
            index="date_created",
            columns="machine_id",
            values=col).resample("3H", closed="left", label="right").std().unstack()
        for col in fields
    ]


    telemetry_sd_3h = pd.concat(temp, axis=1)
    telemetry_sd_3h.columns = [i + "sd_3h" for i in fields]
    telemetry_sd_3h.reset_index(inplace=True)


    temp = []
    fields = ["volt", "rotate", "pressure", "vibration"]

    temp = [
        pd.pivot_table(
            telemetry,
            index="date_created",
            columns="machine_id",
            values=col).rolling(window=24).mean().resample("3H", closed="left", label="right").first().unstack()
        for col in fields
    ]


    telemetry_mean_24h = pd.concat(temp, axis=1)
    telemetry_mean_24h.columns = [i + "mean_24h" for i in fields]
    telemetry_mean_24h.reset_index(inplace=True)
    telemetry_mean_24h = telemetry_mean_24h.loc[-telemetry_mean_24h["voltmean_24h"].isnull()]

    temp = []
    fields = ["volt", "rotate", "pressure", "vibration"]

    temp = [
        pd.pivot_table(
            telemetry,
            index="date_created",
            columns="machine_id",
            values=col).rolling(window=24).std().resample("3H", closed="left", label="right").first().unstack(level=-1)
        for col in fields
    ]


    telemetry_sd_24h = pd.concat(temp, axis=1)
    telemetry_sd_24h.columns = [i + "sd_24h" for i in fields]
    telemetry_sd_24h.reset_index(inplace=True)
    telemetry_sd_24h = telemetry_sd_24h.loc[-telemetry_sd_24h["voltsd_24h"].isnull()]


    telemetry_feat = pd.concat([
        telemetry_mean_3h,
        telemetry_sd_3h.iloc[:, 2:6],
        telemetry_mean_24h.iloc[:, 2:6],
        telemetry_sd_24h.iloc[:, 2:6]], axis=1).dropna()


    error_count = pd.get_dummies(errors)
    error_count.columns = ["date_created", "machine_id", "error1", "error2", "error3", "error4", "error5"]


    error_count_grouped = error_count.groupby(["machine_id", "date_created"]).sum().reset_index()


    error_count_filtered = telemetry[["date_created", "machine_id"]].merge(
        error_count_grouped,
        on=["machine_id", "date_created"],
        how="left"
    ).fillna(0.0)



    temp = []
    fields = [
        "error%d" % i
        for i in range(1,6)
    ]

    temp = [
        pd.pivot_table(
            error_count_filtered,
            index="date_created",
            columns="machine_id",
            values=col).rolling(window=24).sum().resample("3H", closed="left", label="right").first().unstack()
        for col in fields
    ]


    error_count_total = pd.concat(temp, axis=1)
    error_count_total.columns = [i + "count" for i in fields]
    error_count_total.reset_index(inplace=True)
    error_count_total = error_count_total.dropna()


    comp_rep = pd.get_dummies(maint)
    comp_rep.columns = ["date_created", "machine_id", "comp1", "comp2", "comp3", "comp4"]


    comp_rep = comp_rep.groupby(["machine_id", "date_created"]).sum().reset_index()


    comp_rep = telemetry[["date_created", "machine_id"]].merge(
        comp_rep,
        on=["date_created", "machine_id"],
        how="outer").fillna(0).sort_values(by=["machine_id", "date_created"]
    )



    components = ["comp1", "comp2", "comp3", "comp4"]
    for comp in components:

        comp_rep.loc[comp_rep[comp] < 1, comp] = None 

        comp_rep.loc[-comp_rep[comp].isnull(), comp] = comp_rep.loc[-comp_rep[comp].isnull(), "date_created"]

        comp_rep[comp] = pd.to_datetime(comp_rep[comp].fillna(method="ffill"))

    comp_rep = comp_rep.loc[comp_rep["date_created"] > pd.to_datetime("2015-01-01")]


    for comp in components: comp_rep[comp] = (comp_rep["date_created"] - pd.to_datetime(comp_rep[comp])) / np.timedelta64(1, "D")


    final_feat = telemetry_feat.merge(error_count_total, on=["date_created", "machine_id"], how="left")
    final_feat = final_feat.merge(comp_rep, on=["date_created", "machine_id"], how="left")
    final_feat = final_feat.merge(machines, on=["machine_id"], how="left")



    labeled_features = final_feat.merge(failures, on=["date_created", "machine_id"], how="left")


    labeled_features["failure"] = labeled_features["failure"].astype(object).fillna(method="bfill", limit=7)
    labeled_features["failure"] = labeled_features["failure"].fillna("none")
    labeled_features["failure"] = labeled_features["failure"].astype("category")





    model_dummies = pd.get_dummies(labeled_features["model"])
    labeled_features = pd.concat([labeled_features, model_dummies], axis=1)
    labeled_features.drop("model", axis=1, inplace=True)



    threshold_dates = [
        pd.to_datetime("2015-09-30 01:00:00"), pd.to_datetime("2015-10-01 01:00:00")
    ]


    test_results = []

#    total = len(threshold_dates)


    last_train_date = threshold_dates[0]
    first_test_date = threshold_dates[1]


#    ntraining = labeled_features.loc[labeled_features["date_created"] < last_train_date]
#    ntesting = labeled_features.loc[labeled_features["date_created"] > first_test_date]
#
#
#    fails_train = ntraining[ntraining["failure"] != "none"].shape[0]
#    no_fails_train = ntraining[ntraining["failure"] == "none"].shape[0]
#    fails_test = ntesting[ntesting["failure"] != "none"].shape[0]
#    no_fails_test = ntesting[ntesting["failure"] == "none"].shape[0]


#    train_y = labeled_features.loc[labeled_features["date_created"] < last_train_date, "failure"]
#    train_X = labeled_features.loc[labeled_features["date_created"] < last_train_date].drop(["date_created", "machine_id", "failure"], axis=1)

    test_y = labeled_features.loc[labeled_features["date_created"] > first_test_date, "failure"]
    test_X = labeled_features.loc[labeled_features["date_created"] > first_test_date].drop(["date_created", "machine_id", "failure"], axis=1)

#    return [test_y, test_X]


#def trainX(data):
#    model = xgb(n_jobs=-1)
#    model.fit(train_X, train_y)
#
#
#    test_result = pd.DataFrame(labeled_features.loc[labeled_features["date_created"] > first_test_date])
#    test_result["predicted_failure"] = model.predict(test_X)
#    test_results.append(test_result)
#
#    gr_test = pd.DataFrame(test_X.values, columns=test_X.columns)
#
#    probas = model.predict_proba(gr_test)
#    prediction = model.predict(gr_test)
#    ordered_classes = np.unique(np.array(test_y))
#
#    results = pd.DataFrame(probas, columns=ordered_classes)
#
#    return results

#def predictX():
    model = xgb.XGBClassifier(n_jobs=-1)
    model.load_model('./static/model.xgb')


    test_result = pd.DataFrame(labeled_features.loc[labeled_features["date_created"] > first_test_date])
    test_result["predicted_failure"] = model.predict(test_X)
    test_results.append(test_result)

    gr_test = pd.DataFrame(test_X.values, columns=test_X.columns)

    probas = model.predict_proba(gr_test)
    prediction = model.predict(gr_test)
    ordered_classes = np.unique(np.array(test_y))

    results = pd.DataFrame(probas, columns=ordered_classes).idxmax(axis=1)

    return results