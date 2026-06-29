import pandas as pd


def total_sales(df: pd.DataFrame) -> float:
    return df["total"].sum()


def total_orders(df: pd.DataFrame) -> int:
    return df["order_id"].nunique()


def avg_ticket(df: pd.DataFrame) -> float:
    orders = total_orders(df)
    return df["total"].sum() / orders if orders > 0 else 0.0


def gross_profit(df: pd.DataFrame) -> float:
    return float(df["gross_profit"].sum())


def gross_profit_rate(df: pd.DataFrame) -> float:
    t = df["total"].sum()
    return df["gross_profit"].sum() / t if t > 0 else 0.0


def foreign_ratio(orders_df: pd.DataFrame) -> float:
    return orders_df["is_foreign"].mean() if len(orders_df) > 0 else 0.0


def avg_ticket_by_foreign(orders_df: pd.DataFrame, is_foreign: bool) -> float:
    subset = orders_df[orders_df["is_foreign"] == int(is_foreign)]
    return float(subset["total"].mean()) if len(subset) > 0 else 0.0
