def res(telemetry, errors, maint, failures, machines)
    import numpy as np
    import pandas as pd
    from xgboost import XGBClassifier as xgb

    # telemetry = pd.read_csv("../input/PdM_telemetry.csv", error_bad_lines=False)
    # errors = pd.read_csv("../input/PdM_errors.csv", error_bad_lines=False)
    # maint = pd.read_csv("../input/PdM_maint.csv", error_bad_lines=False)
    # failures = pd.read_csv("../input/PdM_failures.csv", error_bad_lines=False)
    # machines = pd.read_csv("../input/PdM_machines.csv", error_bad_lines=False)


    telemetry["datetime"] = pd.to_datetime(telemetry["datetime"], format="%Y-%m-%d %H:%M:%S")

    errors["datetime"] = pd.to_datetime(errors["datetime"], format="%Y-%m-%d %H:%M:%S")
    errors["errorID"] = errors["errorID"].astype("category")

    maint["datetime"] = pd.to_datetime(maint["datetime"], format="%Y-%m-%d %H:%M:%S")
    maint["comp"] = maint["comp"].astype("category")

    machines["model"] = machines["model"].astype("category")

    failures["datetime"] = pd.to_datetime(failures["datetime"], format="%Y-%m-%d %H:%M:%S")
    failures["failure"] = failures["failure"].astype("category")


    temp = []
    fields = ["volt", "rotate", "pressure", "vibration"]

    temp = [
        pd.pivot_table(
            telemetry,
            index="datetime",
            columns="machineID",
            values=col).resample("3H", closed="left", label="right").mean().unstack()
        for col in fields
    ]


    telemetry_mean_3h = pd.concat(temp, axis=1)
    telemetry_mean_3h.columns = [col + "mean_3h" for col in fields]
    telemetry_mean_3h.reset_index(inplace=True)


    temp = [
        pd.pivot_table(
            telemetry,
            index="datetime",
            columns="machineID",
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
            index="datetime",
            columns="machineID",
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
            index="datetime",
            columns="machineID",
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
    error_count.columns = ["datetime", "machineID", "error1", "error2", "error3", "error4", "error5"]


    error_count_grouped = error_count.groupby(["machineID", "datetime"]).sum().reset_index()


    error_count_filtered = telemetry[["datetime", "machineID"]].merge(
        error_count_grouped,
        on=["machineID", "datetime"],
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
            index="datetime",
            columns="machineID",
            values=col).rolling(window=24).sum().resample("3H", closed="left", label="right").first().unstack()
        for col in fields
    ]


    error_count_total = pd.concat(temp, axis=1)
    error_count_total.columns = [i + "count" for i in fields]
    error_count_total.reset_index(inplace=True)
    error_count_total = error_count_total.dropna()


    comp_rep = pd.get_dummies(maint)
    comp_rep.columns = ["datetime", "machineID", "comp1", "comp2", "comp3", "comp4"]


    comp_rep = comp_rep.groupby(["machineID", "datetime"]).sum().reset_index()


    comp_rep = telemetry[["datetime", "machineID"]].merge(
        comp_rep,
        on=["datetime", "machineID"],
        how="outer").fillna(0).sort_values(by=["machineID", "datetime"]
    )



    components = ["comp1", "comp2", "comp3", "comp4"]
    for comp in components:

        comp_rep.loc[comp_rep[comp] < 1, comp] = None 

        comp_rep.loc[-comp_rep[comp].isnull(), comp] = comp_rep.loc[-comp_rep[comp].isnull(), "datetime"]

        comp_rep[comp] = pd.to_datetime(comp_rep[comp].fillna(method="ffill"))

    comp_rep = comp_rep.loc[comp_rep["datetime"] > pd.to_datetime("2015-01-01")]


    for comp in components: comp_rep[comp] = (comp_rep["datetime"] - pd.to_datetime(comp_rep[comp])) / np.timedelta64(1, "D")


    final_feat = telemetry_feat.merge(error_count_total, on=["datetime", "machineID"], how="left")
    final_feat = final_feat.merge(comp_rep, on=["datetime", "machineID"], how="left")
    final_feat = final_feat.merge(machines, on=["machineID"], how="left")



    labeled_features = final_feat.merge(failures, on=["datetime", "machineID"], how="left")


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
    models = []
    total = len(threshold_dates)


    last_train_date = threshold_dates[0]
    first_test_date = threshold_dates[1]


    ntraining = labeled_features.loc[labeled_features["datetime"] < last_train_date]
    ntesting = labeled_features.loc[labeled_features["datetime"] > first_test_date]


    fails_train = ntraining[ntraining["failure"] != "none"].shape[0]
    no_fails_train = ntraining[ntraining["failure"] == "none"].shape[0]
    fails_test = ntesting[ntesting["failure"] != "none"].shape[0]
    no_fails_test = ntesting[ntesting["failure"] == "none"].shape[0]


    train_y = labeled_features.loc[labeled_features["datetime"] < last_train_date, "failure"]
    train_X = labeled_features.loc[labeled_features["datetime"] < last_train_date].drop(["datetime",
                                                                                    "machineID",
                                                                                    "failure"], axis=1)
    test_y = labeled_features.loc[labeled_features["datetime"] > first_test_date, "failure"]
    test_X = labeled_features.loc[labeled_features["datetime"] > first_test_date].drop(["datetime",
                                                                                   "machineID",
                                                                                   "failure"], axis=1)

    model = xgb(n_jobs=-1)
    model.fit(train_X, train_y)


    test_result = pd.DataFrame(labeled_features.loc[labeled_features["datetime"] > first_test_date])
    test_result["predicted_failure"] = model.predict(test_X)
    test_results.append(test_result)
    models.append(model)


    results = pd.DataFrame(probas, columns=ordered_classes)

    return results