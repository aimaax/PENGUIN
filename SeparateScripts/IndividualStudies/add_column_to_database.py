import pandas as pd


# import the database
df = pd.read_pickle("Diodes_Database.pkl")

# print all columns
print(df.columns)

# add a new column called "upper_fit_params_TCT" and "upper_fit_params_CV" and specify that the type should be a tuple of 3 floats
df["upper_fit_params_TCT"] = None
df["upper_fit_params_CV"] = None

# save the database
df.to_pickle("Diodes_Database.pkl")