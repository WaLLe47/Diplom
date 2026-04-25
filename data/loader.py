import pandas as pd


def load_csv(path):

    df = pd.read_csv(path)

    if "x" not in df.columns or "y" not in df.columns:
        raise ValueError(
            "CSV должен содержать x,y"
        )

    x=df["x"].tolist()
    y=df["y"].tolist()

    return x,y