from itertools import combinations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from common.constants import EXCLUDED_ITEMS

_PRIMARY = "#4C78A8"
_SECONDARY = "#F58518"
_WEEKDAY_ORDER = ["月", "火", "水", "木", "金", "土", "日"]
_YEN_AXIS = dict(tickformat=",.0f", tickprefix="¥")
_EXCLUDED_NOTE = "<br><sup>※ オリジナル紙袋など袋類は除外</sup>"


def _excl(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["item_name"].isin(EXCLUDED_ITEMS)]


def daily_sales_line(df: pd.DataFrame) -> go.Figure:
    daily = df.groupby("order_date")["total"].sum().reset_index()
    fig = px.line(
        daily, x="order_date", y="total",
        title="日別売上推移",
        labels={"order_date": "日付", "total": "売上 (円)"},
    )
    avg = daily["total"].mean()
    fig.add_hline(
        y=avg, line_dash="dash", line_color="gray",
        annotation_text=f"平均 ¥{avg:,.0f}",
        annotation_position="top right",
    )
    fig.update_yaxes(**_YEN_AXIS)
    return fig


def hourly_bar(df: pd.DataFrame) -> go.Figure:
    hourly = (
        df.groupby("hour")
        .agg(total=("total", "sum"), count=("order_id", "count"))
        .reset_index()
    )
    fig = go.Figure()
    fig.add_bar(x=hourly["hour"], y=hourly["total"], name="売上", marker_color=_PRIMARY)
    fig.add_scatter(
        x=hourly["hour"], y=hourly["count"],
        name="客数", mode="lines+markers",
        yaxis="y2", line=dict(color=_SECONDARY),
    )
    fig.update_layout(
        title="時間帯別売上・客数",
        xaxis=dict(title="時間帯", dtick=1),
        yaxis=dict(title="売上 (円)", tickformat=",.0f", tickprefix="¥"),
        yaxis2=dict(title="客数", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def weekday_sales_bar(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby("weekday_name")
        .agg(total=("total", "sum"), count=("order_id", "count"))
        .reindex(_WEEKDAY_ORDER)
        .reset_index()
    )
    fig = go.Figure()
    fig.add_bar(x=agg["weekday_name"], y=agg["total"], name="売上", marker_color=_PRIMARY)
    fig.add_scatter(
        x=agg["weekday_name"], y=agg["count"],
        name="客数", mode="lines+markers",
        yaxis="y2", line=dict(color=_SECONDARY),
    )
    fig.update_layout(
        title="曜日別売上・客数",
        xaxis=dict(title="曜日"),
        yaxis=dict(title="売上 (円)", tickformat=",.0f", tickprefix="¥"),
        yaxis2=dict(title="客数", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def weekday_hourly_heatmap(df: pd.DataFrame) -> go.Figure:
    pivot = (
        df.groupby(["weekday_name", "hour"])["order_id"]
        .count()
        .unstack(fill_value=0)
        .reindex(_WEEKDAY_ORDER)
    )
    return px.imshow(
        pivot, text_auto=True,
        title="時間帯×曜日 客数ヒートマップ",
        labels={"x": "時間帯", "y": "曜日", "color": "客数"},
        color_continuous_scale="Blues",
    )


def payment_donut(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=["現金", "カード"],
        values=[df["cash_recieved"].sum(), df["card_recieved"].sum()],
        hole=0.5,
    ))
    fig.update_layout(title="現金/カード比率")
    return fig


def monthly_gp_rate_line(df: pd.DataFrame) -> go.Figure:
    monthly = (
        df.groupby("year_month")
        .apply(lambda x: x["gross_profit"].sum() / x["total"].sum() if x["total"].sum() > 0 else 0)
        .reset_index(name="gp_rate")
    )
    monthly["year_month"] = monthly["year_month"].astype(str)
    fig = px.line(
        monthly, x="year_month", y="gp_rate",
        title="月別粗利率推移",
        labels={"year_month": "年月", "gp_rate": "粗利率"},
        markers=True,
        text="gp_rate",
    )
    fig.update_traces(texttemplate="%{y:.1%}", textposition="top center")
    fig.update_yaxes(tickformat=".1%")
    return fig


def nationality_count_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    counts = df["nationality"].value_counts().head(top_n).reset_index()
    counts.columns = ["nationality", "count"]
    return px.bar(
        counts, x="count", y="nationality", orientation="h",
        title=f"国籍別来客数 TOP{top_n}",
        labels={"count": "件数", "nationality": "国籍"},
        text_auto=True,
    )


def nationality_ticket_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    agg = (
        df.groupby("nationality")
        .agg(avg_total=("total", "mean"), count=("order_id", "count"))
        .reset_index()
        .nlargest(top_n, "avg_total")
    )
    fig = px.bar(
        agg, x="avg_total", y="nationality", orientation="h",
        title=f"国籍別客単価 TOP{top_n}",
        labels={"avg_total": "平均客単価 (円)", "nationality": "国籍"},
        hover_data={"count": True},
        text_auto=",.0f",
    )
    fig.update_xaxes(**_YEN_AXIS)
    return fig


def nationality_hour_heatmap(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    top_nats = df["nationality"].value_counts().head(top_n).index
    subset = df[df["nationality"].isin(top_nats)]
    pivot = (
        subset.groupby(["nationality", "hour"])["order_id"]
        .count()
        .unstack(fill_value=0)
    )
    return px.imshow(
        pivot, text_auto=True,
        title=f"国籍×時間帯 来客数 (TOP{top_n}国籍)",
        labels={"x": "時間帯", "y": "国籍", "color": "客数"},
        color_continuous_scale="Oranges",
    )


def gender_age_heatmap(df: pd.DataFrame) -> go.Figure:
    pivot = df.groupby(["gender", "age_gen"]).size().unstack(fill_value=0)
    return px.imshow(
        pivot, text_auto=True,
        title="性別×年代 ヒートマップ",
        labels={"x": "年代", "y": "性別", "color": "件数"},
    )


def nationality_category_heatmap(items_df: pd.DataFrame) -> go.Figure:
    pivot = (
        _excl(items_df).groupby(["nationality", "department_name"])["after_discount_total"]
        .sum()
        .unstack(fill_value=0)
    )
    return px.imshow(
        pivot, text_auto=True,
        title="国籍×カテゴリ クロス分析",
        labels={"x": "カテゴリ", "y": "国籍", "color": "売上 (円)"},
    )


def foreign_ratio_monthly(df: pd.DataFrame) -> go.Figure:
    monthly = (
        df.groupby("year_month")["is_foreign"]
        .mean()
        .mul(100)
        .reset_index(name="foreign_ratio")
    )
    monthly["year_month"] = monthly["year_month"].astype(str)
    fig = px.bar(
        monthly, x="year_month", y="foreign_ratio",
        title="外国人比率 月次推移",
        labels={"year_month": "年月", "foreign_ratio": "外国人比率 (%)"},
        text_auto=".1f",
    )
    fig.update_yaxes(ticksuffix="%")
    return fig


def category_sales_bar(items_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    agg = (
        _excl(items_df).groupby("department_name")["after_discount_total"]
        .sum()
        .nlargest(top_n)
        .reset_index()
    )
    fig = px.bar(
        agg, x="after_discount_total", y="department_name", orientation="h",
        title=f"カテゴリ別売上ランキング TOP{top_n}{_EXCLUDED_NOTE}",
        labels={"after_discount_total": "売上 (円)", "department_name": "カテゴリ"},
        text_auto=",.0f",
    )
    fig.update_xaxes(**_YEN_AXIS)
    return fig


def sales_gp_bubble(items_df: pd.DataFrame) -> go.Figure:
    agg = (
        _excl(items_df).groupby("department_name")
        .agg(revenue=("after_discount_total", "sum"), cost=("cost_total", "sum"), qty=("item_number", "sum"))
        .reset_index()
    )
    agg["gp_rate"] = (agg["revenue"] - agg["cost"]) / agg["revenue"].replace(0, float("nan"))

    med_rev = agg["revenue"].median()
    med_gp = agg["gp_rate"].median()
    agg["quadrant"] = agg.apply(
        lambda r: "高売上×高粗利" if r["revenue"] >= med_rev and r["gp_rate"] >= med_gp
        else ("高売上×低粗利" if r["revenue"] >= med_rev
              else ("低売上×高粗利" if r["gp_rate"] >= med_gp else "低売上×低粗利")),
        axis=1,
    )

    color_map = {
        "高売上×高粗利": "#2ecc71",
        "高売上×低粗利": "#e67e22",
        "低売上×高粗利": "#3498db",
        "低売上×低粗利": "#bdc3c7",
    }

    fig = px.scatter(
        agg, x="revenue", y="gp_rate", size="qty",
        color="quadrant", color_discrete_map=color_map,
        hover_name="department_name",
        hover_data={"revenue": ":,.0f", "gp_rate": ":.1%", "qty": ":,.0f", "quadrant": False},
        title=f"売上×粗利率 バブルチャート（バブルサイズ=販売数量）{_EXCLUDED_NOTE}",
        labels={"revenue": "売上 (円)", "gp_rate": "粗利率", "qty": "販売数量", "quadrant": "象限"},
        log_x=True,
    )
    fig.update_traces(marker_opacity=0.75)
    fig.update_yaxes(tickformat=".0%")
    fig.update_xaxes(**_YEN_AXIS)
    return fig


def item_sales_bar(items_df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    agg = (
        items_df[~items_df["item_name"].isin(EXCLUDED_ITEMS)]
        .groupby("item_name")["item_number"]
        .sum()
        .nlargest(top_n)
        .reset_index()
    )
    return px.bar(
        agg, x="item_number", y="item_name", orientation="h",
        title=f"商品別販売数 TOP{top_n}<br><sup>※ オリジナル紙袋など袋類は除外</sup>",
        labels={"item_number": "販売数量", "item_name": "商品名"},
        text_auto=True,
    )


def item_revenue_bar(items_df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    agg = (
        items_df[~items_df["item_name"].isin(EXCLUDED_ITEMS)]
        .groupby("item_name")["after_discount_total"]
        .sum()
        .nlargest(top_n)
        .reset_index()
    )
    fig = px.bar(
        agg, x="after_discount_total", y="item_name", orientation="h",
        title=f"商品別売上金額 TOP{top_n}<br><sup>※ オリジナル紙袋など袋類は除外</sup>",
        labels={"after_discount_total": "売上 (円)", "item_name": "商品名"},
        text_auto=",.0f",
    )
    fig.update_xaxes(**_YEN_AXIS)
    return fig


def category_gp_bar(items_df: pd.DataFrame) -> go.Figure:
    agg = (
        _excl(items_df).groupby("department_name")
        .agg(revenue=("after_discount_total", "sum"), cost=("cost_total", "sum"))
        .reset_index()
    )
    agg["gp_rate"] = (agg["revenue"] - agg["cost"]) / agg["revenue"].replace(0, float("nan"))
    agg = agg.dropna(subset=["gp_rate"]).sort_values("gp_rate", ascending=True)
    fig = px.bar(
        agg, x="gp_rate", y="department_name", orientation="h",
        title=f"カテゴリ別粗利率比較{_EXCLUDED_NOTE}",
        labels={"gp_rate": "粗利率", "department_name": "カテゴリ"},
        text_auto=".1%",
    )
    fig.update_xaxes(tickformat=".1%")
    return fig


def category_nationality_stacked(items_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    items_df = _excl(items_df)
    top_cats = items_df.groupby("department_name")["after_discount_total"].sum().nlargest(top_n).index
    subset = items_df[items_df["department_name"].isin(top_cats)]
    agg = (
        subset.groupby(["department_name", "nationality"])["after_discount_total"]
        .sum()
        .reset_index()
    )
    cat_order = (
        agg.groupby("department_name")["after_discount_total"].sum()
        .sort_values(ascending=True).index.tolist()
    )
    fig = px.bar(
        agg, x="after_discount_total", y="department_name", color="nationality",
        orientation="h",
        title=f"カテゴリ別 国籍構成 TOP{top_n}{_EXCLUDED_NOTE}",
        labels={"after_discount_total": "売上 (円)", "department_name": "カテゴリ", "nationality": "国籍"},
        category_orders={"department_name": cat_order},
    )
    fig.update_xaxes(**_YEN_AXIS)
    return fig


def nationality_top_categories(items_df: pd.DataFrame, nationality: str, top_n: int = 10) -> go.Figure:
    subset = _excl(items_df)
    subset = subset[subset["nationality"] == nationality]
    agg = (
        subset.groupby("department_name")
        .agg(revenue=("after_discount_total", "sum"), qty=("item_number", "sum"))
        .reset_index()
        .nlargest(top_n, "revenue")
        .sort_values("revenue", ascending=True)
    )
    fig = px.bar(
        agg, x="revenue", y="department_name", orientation="h",
        title=f"{nationality} の人気カテゴリ TOP{top_n}{_EXCLUDED_NOTE}",
        labels={"revenue": "売上 (円)", "department_name": "カテゴリ"},
        text_auto=",.0f",
        hover_data={"qty": True},
    )
    fig.update_xaxes(**_YEN_AXIS)
    return fig


def nationality_top_items(items_df: pd.DataFrame, nationality: str, top_n: int = 15) -> go.Figure:
    subset = items_df[
        (items_df["nationality"] == nationality) &
        (~items_df["item_name"].isin(EXCLUDED_ITEMS))
    ]
    agg = (
        subset.groupby("item_name")
        .agg(revenue=("after_discount_total", "sum"), qty=("item_number", "sum"))
        .reset_index()
        .nlargest(top_n, "revenue")
        .sort_values("revenue", ascending=True)
    )
    fig = px.bar(
        agg, x="revenue", y="item_name", orientation="h",
        title=f"{nationality} の人気商品 TOP{top_n}（売上金額）<br><sup>※ オリジナル紙袋など袋類は除外</sup>",
        labels={"revenue": "売上 (円)", "item_name": "商品名"},
        text_auto=",.0f",
        hover_data={"qty": True},
    )
    fig.update_xaxes(**_YEN_AXIS)
    return fig


def nationality_top_items_count(items_df: pd.DataFrame, nationality: str, top_n: int = 15) -> go.Figure:
    subset = items_df[
        (items_df["nationality"] == nationality) &
        (~items_df["item_name"].isin(EXCLUDED_ITEMS))
    ]
    agg = (
        subset.groupby("item_name")["item_number"]
        .sum()
        .nlargest(top_n)
        .reset_index()
        .sort_values("item_number", ascending=True)
    )
    return px.bar(
        agg, x="item_number", y="item_name", orientation="h",
        title=f"{nationality} の人気商品 TOP{top_n}（販売数）<br><sup>※ オリジナル紙袋など袋類は除外</sup>",
        labels={"item_number": "販売数量", "item_name": "商品名"},
        text_auto=True,
    )


def nationality_category_monthly(items_df: pd.DataFrame, nationality: str, top_n: int = 5) -> go.Figure:
    subset = _excl(items_df)
    subset = subset[subset["nationality"] == nationality].copy()
    top_cats = subset.groupby("department_name")["after_discount_total"].sum().nlargest(top_n).index
    subset = subset[subset["department_name"].isin(top_cats)]
    subset["year_month"] = subset["year_month"].astype(str)
    monthly = (
        subset.groupby(["year_month", "department_name"])["after_discount_total"]
        .sum()
        .reset_index()
    )
    fig = px.line(
        monthly, x="year_month", y="after_discount_total",
        color="department_name", markers=True,
        title=f"{nationality} カテゴリ別売上推移 TOP{top_n}",
        labels={"year_month": "年月", "after_discount_total": "売上 (円)", "department_name": "カテゴリ"},
    )
    fig.update_yaxes(**_YEN_AXIS)
    return fig


def category_monthly_trend(items_df: pd.DataFrame, top_n: int = 5) -> go.Figure:
    items_df = _excl(items_df)
    top_cats = items_df.groupby("department_name")["after_discount_total"].sum().nlargest(top_n).index
    subset = items_df[items_df["department_name"].isin(top_cats)].copy()
    subset["year_month"] = subset["year_month"].astype(str)
    monthly = (
        subset.groupby(["year_month", "department_name"])["after_discount_total"]
        .sum()
        .reset_index()
    )
    fig = px.line(
        monthly, x="year_month", y="after_discount_total",
        color="department_name",
        title=f"カテゴリ別売上推移 TOP{top_n}{_EXCLUDED_NOTE}",
        labels={"year_month": "年月", "after_discount_total": "売上 (円)", "department_name": "カテゴリ"},
        markers=True,
    )
    fig.update_yaxes(**_YEN_AXIS)
    return fig


# ── ABC分析 ──────────────────────────────────────────────────────────────────

def abc_category_bar(items_df: pd.DataFrame) -> go.Figure:
    df = _excl(items_df)
    df = df[df["department_name"].notna() & (df["department_name"].str.strip() != "")]
    agg = (
        df.groupby("department_name")["after_discount_total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index(name="revenue")
    )
    total = agg["revenue"].sum()
    agg["cumulative_pct"] = agg["revenue"].cumsum() / total * 100
    agg["class"] = agg["cumulative_pct"].apply(
        lambda x: "A（〜80%）" if x <= 80 else ("B（80〜95%）" if x <= 95 else "C（95〜100%）")
    )
    _cls_color = {"A（〜80%）": "#2ecc71", "B（80〜95%）": "#f39c12", "C（95〜100%）": "#bdc3c7"}

    fig = go.Figure()
    fig.add_bar(
        x=agg["department_name"], y=agg["revenue"],
        marker_color=[_cls_color[c] for c in agg["class"]],
        name="売上",
        customdata=agg[["class", "cumulative_pct"]].values,
        hovertemplate="%{x}<br>売上: ¥%{y:,.0f}<br>クラス: %{customdata[0]}<br>累積: %{customdata[1]:.1f}%<extra></extra>",
    )
    fig.add_scatter(
        x=agg["department_name"], y=agg["cumulative_pct"],
        name="累積構成比", mode="lines+markers",
        yaxis="y2", line=dict(color="red", width=2),
    )
    fig.add_hline(y=80, line_dash="dash", line_color="#2ecc71", yref="y2",
                  annotation_text="80% (A/B)", annotation_position="top right")
    fig.add_hline(y=95, line_dash="dash", line_color="#f39c12", yref="y2",
                  annotation_text="95% (B/C)", annotation_position="top right")
    fig.update_layout(
        title=f"カテゴリ ABC分析（売上構成）{_EXCLUDED_NOTE}",
        xaxis=dict(title="カテゴリ"),
        yaxis=dict(title="売上 (円)", tickformat=",.0f", tickprefix="¥"),
        yaxis2=dict(title="累積構成比 (%)", overlaying="y", side="right", range=[0, 112], ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def abc_item_bar(items_df: pd.DataFrame, top_n: int = 30) -> go.Figure:
    df = _excl(items_df)
    agg = (
        df.groupby("item_name")["after_discount_total"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index(name="revenue")
    )
    total = agg["revenue"].sum()
    agg["cumulative_pct"] = agg["revenue"].cumsum() / total * 100
    agg["class"] = agg["cumulative_pct"].apply(
        lambda x: "A（〜80%）" if x <= 80 else ("B（80〜95%）" if x <= 95 else "C（95〜100%）")
    )
    _cls_color = {"A（〜80%）": "#2ecc71", "B（80〜95%）": "#f39c12", "C（95〜100%）": "#bdc3c7"}

    fig = go.Figure()
    fig.add_bar(
        x=agg["item_name"], y=agg["revenue"],
        marker_color=[_cls_color[c] for c in agg["class"]],
        name="売上",
        customdata=agg[["class", "cumulative_pct"]].values,
        hovertemplate="%{x}<br>売上: ¥%{y:,.0f}<br>クラス: %{customdata[0]}<br>累積: %{customdata[1]:.1f}%<extra></extra>",
    )
    fig.add_scatter(
        x=agg["item_name"], y=agg["cumulative_pct"],
        name="累積構成比", mode="lines+markers",
        yaxis="y2", line=dict(color="red", width=2),
    )
    fig.add_hline(y=80, line_dash="dash", line_color="#2ecc71", yref="y2",
                  annotation_text="80%", annotation_position="top right")
    fig.add_hline(y=95, line_dash="dash", line_color="#f39c12", yref="y2",
                  annotation_text="95%", annotation_position="top right")
    fig.update_layout(
        title=f"商品 ABC分析（売上 TOP{top_n}）{_EXCLUDED_NOTE}",
        xaxis=dict(title="商品名", tickangle=45),
        yaxis=dict(title="売上 (円)", tickformat=",.0f", tickprefix="¥"),
        yaxis2=dict(title="累積構成比 (%)", overlaying="y", side="right", range=[0, 112], ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ── 粗利額ランキング ─────────────────────────────────────────────────────────

def category_gp_amount_bar(items_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    df = _excl(items_df)
    df = df[df["department_name"].notna() & (df["department_name"].str.strip() != "")]
    agg = (
        df.groupby("department_name")
        .agg(revenue=("after_discount_total", "sum"), cost=("cost_total", "sum"))
        .reset_index()
    )
    agg["gp_amount"] = agg["revenue"] - agg["cost"]
    agg["gp_rate"] = agg["gp_amount"] / agg["revenue"].replace(0, float("nan"))
    agg = agg.nlargest(top_n, "gp_amount").sort_values("gp_amount", ascending=True)
    fig = px.bar(
        agg, x="gp_amount", y="department_name", orientation="h",
        title=f"カテゴリ別粗利額 TOP{top_n}{_EXCLUDED_NOTE}",
        labels={"gp_amount": "粗利額 (円)", "department_name": "カテゴリ", "gp_rate": "粗利率"},
        color="gp_rate", color_continuous_scale="RdYlGn",
        hover_data={"gp_rate": ":.1%", "revenue": ":,.0f"},
        text_auto=",.0f",
    )
    fig.update_xaxes(**_YEN_AXIS)
    fig.update_coloraxes(colorbar_tickformat=".0%", colorbar_title="粗利率")
    return fig


def item_gp_amount_bar(items_df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    df = _excl(items_df)
    agg = (
        df.groupby("item_name")
        .agg(revenue=("after_discount_total", "sum"), cost=("cost_total", "sum"))
        .reset_index()
    )
    agg["gp_amount"] = agg["revenue"] - agg["cost"]
    agg["gp_rate"] = agg["gp_amount"] / agg["revenue"].replace(0, float("nan"))
    agg = agg.nlargest(top_n, "gp_amount").sort_values("gp_amount", ascending=True)
    fig = px.bar(
        agg, x="gp_amount", y="item_name", orientation="h",
        title=f"商品別粗利額 TOP{top_n}{_EXCLUDED_NOTE}",
        labels={"gp_amount": "粗利額 (円)", "item_name": "商品名", "gp_rate": "粗利率"},
        color="gp_rate", color_continuous_scale="RdYlGn",
        hover_data={"gp_rate": ":.1%", "revenue": ":,.0f"},
        text_auto=",.0f",
    )
    fig.update_xaxes(**_YEN_AXIS)
    fig.update_coloraxes(colorbar_tickformat=".0%", colorbar_title="粗利率")
    return fig


# ── 客単価分布・時間帯効率 ────────────────────────────────────────────────────

def ticket_histogram(orders_df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        orders_df, x="total", nbins=30,
        title="客単価分布",
        labels={"total": "客単価 (円)"},
        color_discrete_sequence=[_PRIMARY],
    )
    median_val = orders_df["total"].median()
    avg_val = orders_df["total"].mean()
    fig.add_vline(x=median_val, line_dash="dash", line_color="red",
                  annotation_text=f"中央値 ¥{median_val:,.0f}", annotation_position="top left")
    fig.add_vline(x=avg_val, line_dash="dot", line_color="orange",
                  annotation_text=f"平均 ¥{avg_val:,.0f}", annotation_position="top right")
    fig.update_xaxes(**_YEN_AXIS)
    fig.update_yaxes(title="注文数")
    return fig


def hourly_efficiency_bar(orders_df: pd.DataFrame) -> go.Figure:
    agg = (
        orders_df.groupby("hour")
        .agg(total=("total", "sum"), count=("order_id", "count"))
        .reset_index()
    )
    agg["efficiency"] = agg["total"] / agg["count"].replace(0, float("nan"))
    fig = go.Figure()
    fig.add_bar(x=agg["hour"], y=agg["efficiency"], name="売上効率 (¥/人)", marker_color=_PRIMARY)
    fig.add_scatter(
        x=agg["hour"], y=agg["count"],
        name="客数", mode="lines+markers",
        yaxis="y2", line=dict(color=_SECONDARY),
    )
    fig.update_layout(
        title="時間帯別 売上効率（売上÷客数）",
        xaxis=dict(title="時間帯", dtick=1),
        yaxis=dict(title="売上効率 (円/人)", tickformat=",.0f", tickprefix="¥"),
        yaxis2=dict(title="客数", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ── まとめ買い分析 ────────────────────────────────────────────────────────────

def basket_size_dist(items_df: pd.DataFrame, orders_df: pd.DataFrame) -> go.Figure:
    basket = items_df.groupby("order_id")["item_name"].nunique().reset_index(name="basket_size")
    basket["label"] = basket["basket_size"].apply(
        lambda x: "1種類" if x == 1 else ("2種類" if x == 2 else ("3種類" if x == 3 else "4種類以上"))
    )
    order_cat = ["1種類", "2種類", "3種類", "4種類以上"]
    counts = basket["label"].value_counts().reindex(order_cat).fillna(0).reset_index()
    counts.columns = ["label", "count"]
    counts["pct"] = counts["count"] / counts["count"].sum() * 100
    fig = px.bar(
        counts, x="label", y="count",
        title="購買商品種類数分布（1注文あたり）",
        labels={"label": "購買種類数", "count": "注文数"},
        text=counts["pct"].apply(lambda x: f"{x:.1f}%"),
        color="label",
        color_discrete_sequence=[_PRIMARY, _SECONDARY, "#2ecc71", "#e74c3c"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False)
    return fig


def basket_size_vs_ticket(items_df: pd.DataFrame, orders_df: pd.DataFrame) -> go.Figure:
    basket = items_df.groupby("order_id")["item_name"].nunique().reset_index(name="basket_size")
    merged = orders_df[["order_id", "total"]].merge(basket, on="order_id")
    merged["label"] = merged["basket_size"].apply(
        lambda x: "1種類" if x == 1 else ("2種類" if x == 2 else ("3種類" if x == 3 else "4種類以上"))
    )
    order_cat = ["1種類", "2種類", "3種類", "4種類以上"]
    agg = merged.groupby("label")["total"].mean().reindex(order_cat).reset_index()
    agg.columns = ["label", "avg_total"]
    fig = px.bar(
        agg, x="label", y="avg_total",
        title="購買種類数別 平均客単価",
        labels={"label": "購買種類数", "avg_total": "平均客単価 (円)"},
        text_auto=",.0f",
        color="label",
        color_discrete_sequence=[_PRIMARY, _SECONDARY, "#2ecc71", "#e74c3c"],
    )
    fig.update_yaxes(**_YEN_AXIS)
    fig.update_layout(showlegend=False)
    return fig


def basket_size_by_nationality(orders_df: pd.DataFrame, items_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    basket = items_df.groupby("order_id")["item_name"].nunique().reset_index(name="basket_size")
    merged = orders_df[["order_id", "nationality"]].merge(basket, on="order_id")
    top_nats = merged["nationality"].value_counts().head(top_n).index
    agg = (
        merged[merged["nationality"].isin(top_nats)]
        .groupby("nationality")["basket_size"]
        .mean()
        .reset_index()
        .sort_values("basket_size", ascending=True)
    )
    fig = px.bar(
        agg, x="basket_size", y="nationality", orientation="h",
        title=f"国籍別 平均購買種類数 TOP{top_n}",
        labels={"basket_size": "平均購買種類数", "nationality": "国籍"},
        text_auto=".2f",
        color="basket_size", color_continuous_scale="Blues",
    )
    return fig


def category_cooccurrence_heatmap(items_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    df = _excl(items_df)
    df = df[df["department_name"].notna() & (df["department_name"].str.strip() != "")]
    top_cats = df.groupby("department_name")["after_discount_total"].sum().nlargest(top_n).index.tolist()
    df = df[df["department_name"].isin(top_cats)]

    order_cats = df.groupby("order_id")["department_name"].apply(set)
    cooc: dict = {}
    for cats in order_cats:
        cats_in = [c for c in cats if c in top_cats]
        for a, b in combinations(cats_in, 2):
            cooc[(a, b)] = cooc.get((a, b), 0) + 1
            cooc[(b, a)] = cooc.get((b, a), 0) + 1

    matrix = pd.DataFrame(0, index=top_cats, columns=top_cats)
    for (a, b), cnt in cooc.items():
        matrix.loc[a, b] = cnt

    fig = px.imshow(
        matrix, text_auto=True,
        title=f"カテゴリ共購買ヒートマップ TOP{top_n}（同一注文内の同時購買数）{_EXCLUDED_NOTE}",
        labels={"x": "カテゴリ", "y": "カテゴリ", "color": "共購買数"},
        color_continuous_scale="Blues",
        aspect="auto",
    )
    fig.update_xaxes(side="top", tickangle=-35, tickfont=dict(size=12))
    fig.update_yaxes(tickfont=dict(size=12))
    fig.update_layout(
        height=620,
        margin=dict(l=160, r=80, t=160, b=20),
    )
    return fig
