import pandas as pd

def check_multiindex_key(database):
    print("Is MultiIndex:", isinstance(database.index, pd.MultiIndex))
    print("Number of levels:", database.index.nlevels)
    print("Index is unique:", database.index.is_unique)
    print("Index names:", database.index.names)
    print()

    key = (
        '200206_SR_UL',
        'DoubleIrrSRNeutron2025',
        200,
        4e15,
        -20,
        2000,
        r'C:\Users\MaxAn\Documents\Code\CERN\Particulars_Analysis\particulars-analysis\Data\DoubleIrrNeutron2025\\',
        '6days'
    )

    # Count exact matches
    count = (database.index == key).sum()
    print("Exact matches for key:", count)
    print()

    if count > 0:
        print("Rows with this index:")
        print(database.loc[key])
    else:
        print("No rows found with this index.")

    print()
    print("All duplicated MultiIndex entries:")
    dup = database.index[database.index.duplicated(keep=False)]
    print(dup)

    print()
    print("Duplicate counts per index:")
    dup_counts = (
        database
        .groupby(level=database.index.names)
        .size()
        .loc[lambda x: x > 1]
    )
    print(dup_counts)


if __name__ == "__main__":
    df = pd.read_pickle("Diodes_Database.pkl")
    df = df[~df.index.duplicated(keep='first')]
    
    idx = df.index

    mask = (
        (idx.get_level_values('sensor_id') == '200206_SR_UL') &
        (idx.get_level_values('campaign') == 'DoubleIrrSRNeutron2025') &
        (idx.get_level_values('thickness') == 200) &
        (idx.get_level_values('fluence') == 4e15) &
        (idx.get_level_values('temperature') == -20) &
        (idx.get_level_values('CVF') == 2000) &
        (idx.get_level_values('annealing_time') == 'noadd')
    )

    print("Number of matching rows:", mask.sum())

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    index_cols = df.index.names

    print(
        df.reset_index()
        .sort_values(by=["sensor_id", "annealing_time"])
        [df.index.names]
    )

    # save pickle
    df.to_pickle("Diodes_Database.pkl")





    # check_multiindex_key(df)
