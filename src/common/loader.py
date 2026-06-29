import unicodedata

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from common.constants import (
    CACHE_TTL,
    NUMERIC_COLS,
    SECTION_AGE,
    SECTION_GENDER,
    SECTION_NATIONALITY,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

SHEETS_MIME = "application/vnd.google-apps.spreadsheet"


def _list_sheets_in_folder(drive_svc, folder_id: str) -> list[dict]:
    query = f"'{folder_id}' in parents and mimeType='{SHEETS_MIME}' and trashed=false"
    result = drive_svc.files().list(
        q=query,
        fields="files(id, name)",
        orderBy="name",
    ).execute()
    return result.get("files", [])


@st.cache_data(ttl=CACHE_TTL)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict, dict]:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    drive_svc = build("drive", "v3", credentials=creds)

    # 客層マスタ
    master_sh = gc.open_by_key(st.secrets["sheets"]["master_id"])
    master_ws = master_sh.get_worksheet_by_id(int(st.secrets["sheets"]["master_gid"]))
    master = pd.DataFrame(master_ws.get_all_records())

    nat_master = (
        master[master["セクション名"] == SECTION_NATIONALITY]
        .set_index("客層ID")["客層名"].to_dict()
    )
    gender_master = (
        master[master["セクション名"] == SECTION_GENDER]
        .set_index("客層ID")["客層名"].to_dict()
    )
    age_master = (
        master[master["セクション名"] == SECTION_AGE]
        .set_index("客層ID")["客層名"].to_dict()
    )

    # フォルダ内の全Google Sheetsを自動取得して結合
    folder_id = st.secrets["sheets"]["sales_folder_id"]
    files = _list_sheets_in_folder(drive_svc, folder_id)

    if not files:
        raise ValueError(f"フォルダ内にGoogle Sheetsファイルが見つかりません: {folder_id}")

    monthly_dfs = []
    for f in files:
        sh = gc.open_by_key(f["id"])
        ws = sh.get_worksheet(0)  # 先頭シートを使用
        df = pd.DataFrame(ws.get_all_records())
        if not df.empty:
            monthly_dfs.append(df)

    raw = pd.concat(monthly_dfs, ignore_index=True)

    # クリーニング
    df = raw[raw["cancel_div"] == 0].copy()
    df["order_datetime"] = pd.to_datetime(df["order_datetime"])
    df["order_date"] = pd.to_datetime(df["order_date"])
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 注文単位テーブル
    orders_df = df.drop_duplicates("order_id").copy()
    orders_df["hour"] = orders_df["order_datetime"].dt.hour
    orders_df["weekday"] = orders_df["order_datetime"].dt.weekday
    _WEEKDAY_JP = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}
    orders_df["weekday_name"] = orders_df["weekday"].map(_WEEKDAY_JP)
    orders_df["month"] = orders_df["order_date"].dt.month
    orders_df["year_month"] = orders_df["order_date"].dt.to_period("M")
    orders_df["gross_profit"] = orders_df["total"] - orders_df["cost_subtotal"]
    orders_df["gp_rate"] = orders_df["gross_profit"] / orders_df["total"]
    orders_df["is_foreign"] = (orders_df["customer1"] != 1).astype(int)
    orders_df["nationality"] = orders_df["customer1"].map(nat_master)
    orders_df["gender"] = orders_df["customer2"].map(gender_master)
    orders_df["age_gen"] = orders_df["customer3"].map(age_master)

    # 商品明細テーブル
    items_df = df.copy()
    items_df["month"] = items_df["order_date"].dt.month
    items_df["year_month"] = items_df["order_date"].dt.to_period("M")
    items_df["gp_item"] = items_df["after_discount_total"] - items_df["cost_total"]
    items_df["nationality"] = items_df["customer1"].map(nat_master)
    for col in ("item_name", "department_name"):
        items_df[col] = items_df[col].apply(
            lambda x: unicodedata.normalize("NFKC", str(x)) if pd.notna(x) else x
        )

    return orders_df, items_df, nat_master, gender_master, age_master
