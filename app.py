
import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- PAGE SETTINGS ----------------

st.set_page_config(
    page_title="Sales Analytics",
    page_icon="📊",
    layout="wide"
)

# ---------------- DARK THEME ----------------

st.markdown("""
<style>
.stApp {
    background-color: #0B1220;
    color: #F1F5F9;
}
[data-testid="stSidebar"] {
    background-color: #111827;
}
[data-testid="stMetric"] {
    background-color: #151F30;
    border: 1px solid #29364A;
    padding: 18px;
    border-radius: 12px;
}
[data-testid="stMetricLabel"] {
    color: #94A3B8;
}
[data-testid="stMetricValue"] {
    color: #60A5FA;
}
h1, h2, h3 {
    color: #F8FAFC;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------

st.title("📊 Sales Analytics Dashboard")
st.caption("Business performance | Sales, profit and product analysis")
st.divider()

# ---------------- DATA UPLOAD ----------------

uploaded_file = st.sidebar.file_uploader(
    "Upload your sales CSV file",
    type=["csv"]
)

if uploaded_file is None:
    st.info("👈 Upload your cleaned sales CSV file from the sidebar to begin.")
    st.stop()

try:
    df = pd.read_csv(uploaded_file)
except Exception as error:
    st.error(f"Could not read the CSV file: {error}")
    st.stop()

# ---------------- CHECK REQUIRED COLUMNS ----------------

required = [
    "Sales_Amount",
    "Quantity_Sold",
    "Unit_Cost"
]

missing = [col for col in required if col not in df.columns]

if missing:
    st.error(f"These required columns are missing: {missing}")
    st.write("Columns found in your file:", df.columns.tolist())
    st.stop()

# ---------------- CLEAN DATA FOR ANALYSIS ----------------

df = df.copy()

for col in ["Sales_Amount", "Quantity_Sold", "Unit_Cost"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(
    subset=["Sales_Amount", "Quantity_Sold", "Unit_Cost"]
)

# Profit formula follows the existing project logic:
# Profit = Sales Amount - (Quantity Sold * Unit Cost)

df["Total_Cost"] = df["Quantity_Sold"] * df["Unit_Cost"]
df["Profit"] = df["Sales_Amount"] - df["Total_Cost"]

if "Sale_Date" in df.columns:
    df["Sale_Date"] = pd.to_datetime(
        df["Sale_Date"], errors="coerce"
    )

# ---------------- SIDEBAR FILTERS ----------------

st.sidebar.title("Dashboard Filters")
filtered = df.copy()

filter_columns = [
    "Region",
    "Product_Category",
    "Sales_Rep"
]

for col in filter_columns:
    if col in filtered.columns:
        options = sorted(
            filtered[col].dropna().astype(str).unique().tolist()
        )

        selected = st.sidebar.multiselect(
            f"Select {col.replace('_', ' ')}",
            options=options,
            default=options
        )

        filtered = filtered[
            filtered[col].astype(str).isin(selected)
        ]

if "Sale_Date" in filtered.columns:
    valid_dates = filtered["Sale_Date"].dropna()

    if not valid_dates.empty:
        start_date = valid_dates.min().date()
        end_date = valid_dates.max().date()

        date_range = st.sidebar.date_input(
            "Sale date range",
            value=(start_date, end_date),
            min_value=start_date,
            max_value=end_date
        )

        if isinstance(date_range, (tuple, list)):
            if len(date_range) == 2:
                start, end = date_range
                filtered = filtered[
                    filtered["Sale_Date"].dt.date.between(start, end)
                ]

# ---------------- HANDLE EMPTY FILTER RESULTS ----------------

if filtered.empty:
    st.warning("No records match these filters. Change the filters to continue.")
    st.stop()

# ---------------- KPI CARDS ----------------

total_sales = filtered["Sales_Amount"].sum()
total_profit = filtered["Profit"].sum()
total_quantity = filtered["Quantity_Sold"].sum()
average_sale = filtered["Sales_Amount"].mean()

st.subheader("Business Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Sales", f"{total_sales:,.2f}")
c2.metric("Total Profit", f"{total_profit:,.2f}")
c3.metric("Units Sold", f"{total_quantity:,.0f}")
c4.metric("Average Sale / Row", f"{average_sale:,.2f}")

st.caption(
    f"Analysis covers {len(filtered):,} records after applying filters."
)

st.divider()

# ---------------- CHART THEME ----------------

chart_theme = dict(
    template="plotly_dark",
    paper_bgcolor="#151F30",
    plot_bgcolor="#151F30",
    font=dict(color="#E2E8F0"),
    margin=dict(l=20, r=20, t=55, b=20)
)

# ---------------- SALES BY CATEGORY ----------------

left, right = st.columns(2)

with left:
    st.subheader("Sales by Category")

    if "Product_Category" in filtered.columns:
        category_sales = (
            filtered.groupby("Product_Category", dropna=False)
            ["Sales_Amount"].sum().reset_index()
        )

        fig = px.bar(
            category_sales,
            x="Product_Category",
            y="Sales_Amount",
            color="Product_Category",
            title="Revenue by Product Category"
        )

        fig.update_layout(showlegend=False, **chart_theme)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Product_Category column is not available.")

# ---------------- REGIONAL SALES ----------------

with right:
    st.subheader("Regional Performance")

    if "Region" in filtered.columns:
        region_sales = (
            filtered.groupby("Region", dropna=False)
            ["Sales_Amount"].sum().reset_index()
        )

        fig = px.pie(
            region_sales,
            names="Region",
            values="Sales_Amount",
            hole=0.55,
            title="Share of Total Sales"
        )

        fig.update_layout(**chart_theme)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Region column is not available.")

# ---------------- PROFIT BY CATEGORY ----------------

left, right = st.columns(2)

with left:
    st.subheader("Profit Analysis")

    if "Product_Category" in filtered.columns:
        profit_category = (
            filtered.groupby("Product_Category", dropna=False)
            ["Profit"].sum().reset_index()
        )

        fig = px.bar(
            profit_category,
            x="Product_Category",
            y="Profit",
            color="Profit",
            color_continuous_scale="Teal",
            title="Profit by Product Category"
        )

        fig.update_layout(**chart_theme)
        st.plotly_chart(fig, use_container_width=True)

# ---------------- MONTHLY SALES TREND ----------------

with right:
    st.subheader("Monthly Sales Trend")

    if "Sale_Date" in filtered.columns:
        dated = filtered.dropna(subset=["Sale_Date"]).copy()

        if not dated.empty:
            dated["Month"] = (
                dated["Sale_Date"].dt.to_period("M").dt.to_timestamp()
            )

            monthly = (
                dated.groupby("Month")["Sales_Amount"]
                .sum().reset_index()
            )

            fig = px.line(
                monthly,
                x="Month",
                y="Sales_Amount",
                markers=True,
                title="Revenue Over Time"
            )

            fig.update_traces(line=dict(color="#60A5FA", width=3))
            fig.update_layout(**chart_theme)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No valid sale dates are available.")
    else:
        st.info("Sale_Date column is not available.")

# ---------------- AUTOMATIC BUSINESS INSIGHTS ----------------

st.divider()
st.subheader("💡 Business Insights")

if "Product_Category" in filtered.columns:
    category_sales = filtered.groupby("Product_Category")[
        "Sales_Amount"
    ].sum()

    if not category_sales.empty:
        st.write(
            f"**Top sales category:** {category_sales.idxmax()} "
            f"({category_sales.max():,.2f} in sales)"
        )

if "Region" in filtered.columns:
    region_sales = filtered.groupby("Region")["Sales_Amount"].sum()

    if not region_sales.empty:
        st.write(
            f"**Leading region:** {region_sales.idxmax()} "
            f"({region_sales.max():,.2f} in sales)"
        )

if "Product_Category" in filtered.columns:
    category_profit = filtered.groupby("Product_Category")["Profit"].sum()

    if not category_profit.empty:
        st.write(
            f"**Highest total-profit category:** "
            f"{category_profit.idxmax()} "
            f"({category_profit.max():,.2f} profit)"
        )

if "Sales_Rep" in filtered.columns:
    rep_sales = filtered.groupby("Sales_Rep")["Sales_Amount"].sum()

    if not rep_sales.empty:
        st.write(
            f"**Top sales representative by revenue:** "
            f"{rep_sales.idxmax()} "
            f"({rep_sales.max():,.2f} in sales)"
        )

# ---------------- DATA TABLE ----------------

with st.expander("View filtered sales records"):
    st.dataframe(filtered, use_container_width=True)

st.caption("Sales Analytics Dashboard | Sales Data Analysis System")
