import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings("ignore") #To suppress every warning.

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SG Job Market – High Demand / Low Applications",
    page_icon="📈",
    layout="wide",
    
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main {background-color: #f8f9fc;}
    .block-container {padding-top: 1.5rem;}
    h1 {color: #1a1a2e;} 
    h2, h3 {color: #16213e;}
    .metric-card {background: white; border-radius: 10px; padding: 1rem;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center;}
    .stMetric {background: white; border-radius: 10px; padding: .5rem;
               box-shadow: 0 2px 6px rgba(0,0,0,0.07);}
</style>
""", unsafe_allow_html=True)

# ─── Load Data ────────────────────────────────────────────────────────────────
import os #import os allows Python to interact with operating system

@st.cache_data  #Added decorator so that the file is not re-read each rerun to improve performance.
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "sg_job_data_cleaned.csv")
    df = pd.read_csv("/home/wongks-9331485/my-streamlit-app/sg_job_data_cleaned.csv")
    # Explode comma-separated categories into individual rows
    df["categories"] = df["categories"].str.split(",") #split string into list format
    df = df.explode("categories") #explode list into separate rows
    df["categories"] = df["categories"].str.strip() #strip whitespace or empty space
    return df

@st.cache_data
def build_category_stats(df): #Group all by categories - Total 43 categories
    cat = df.groupby("categories").agg(
        total_postings=("metadata_jobPostId", "count"),
        total_applications=("metadata_totalNumberJobApplication", "sum"),
        avg_applications=("metadata_totalNumberJobApplication", "mean"),
        total_views=("metadata_totalNumberOfView", "sum"),
    ).reset_index()
    return cat

df_raw = load_data()
cat_stats = build_category_stats(df_raw)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Flag_of_Singapore.svg/320px-Flag_of_Singapore.svg.png",
    width=80,
)
st.sidebar.title("🎛️ Filter Controls")
st.sidebar.markdown("---")

st.sidebar.subheader("📌 Demand Threshold")
posting_pct = st.sidebar.slider(
    "Minimum postings percentile (demand)",
    min_value=0, max_value=95, value=50, step=5,
    help="Categories with postings above this percentile are considered high-demand.",
)

st.sidebar.subheader("📌 Applications Threshold")
app_pct = st.sidebar.slider(
    "Maximum avg-applications percentile (low interest)",
    min_value=5, max_value=100, value=50, step=5,
    help="Categories with avg applications below this percentile are considered low-application.",
)

st.sidebar.subheader("📊 Chart Settings")
top_n = st.sidebar.slider("Top N categories to display", min_value=5, max_value=40, value=20, step=5)
bar_palette = st.sidebar.selectbox(
    "Bar chart colour palette",
    ["rocket_r", "mako_r", "viridis_r", "Blues_r", "Oranges_r", "Purples_r"],
    index=0,
)
line_palette = st.sidebar.selectbox(
    "Line chart colour",
    ["crimson", "royalblue", "seagreen", "darkorange", "mediumpurple"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.info("Data: Singapore Job Market (Cleaned)")

# ─── Compute thresholds & filter ─────────────────────────────────────────────
'''line 67 posting_pct - for 'demand threshold' side bar setting. 
   e.g. if 50 on 'demand threshold' slider is selected, the median value in cat_stats["total_postings"] is selected.'''
post_thresh = cat_stats["total_postings"].quantile(posting_pct / 100)  

'''line 74 app_pct - for 'application threshold' side bar setting.
   e.g. if 50 on 'Application threshold' slider is selected, the median value in cat_stats["total_postings"] is selected.'''
app_thresh  = cat_stats["avg_applications"].quantile(app_pct / 100) 

filtered = cat_stats[
    (cat_stats["total_postings"] > post_thresh) & 
    (cat_stats["avg_applications"] < app_thresh)
].copy()

# Sum total_applications per unique category  (already grouped) - for bar plot at line 135 to 179
filtered_sorted = filtered.sort_values("total_applications", ascending=False).head(top_n) #Top_n - chart setting sidebar - max 40 categories.

# Shorten very long labels for readability
def shorten(label, max_len=40):
    return label if len(label) <= max_len else label[:max_len-1] + "…"

filtered_sorted["label"] = filtered_sorted["categories"].apply(shorten)

# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🇸🇬 Singapore Job Market Analysis")
st.subheader("High-Demand Categories with Low Job Applications")
st.markdown(
    "Categories that have **many job postings** (high employer demand) "
    "but **few applicants** — revealing talent gaps in Singapore's labour market."
)

# ─── Top KPIs ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("🗂️ Total Categories", f"{len(cat_stats):,}") #length if 'categories" = 43
col2.metric("🔍 Matching Categories", f"{len(filtered):,}") #length of filtered categories
col3.metric("📢 Posting Threshold", f"{int(post_thresh):,} posts") #length of posting converted from string to integer
col4.metric("📥 Avg-App Threshold", f"{app_thresh:.2f} avg") #average application threshold rounded up to 2 decimal places.

st.markdown("---")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Bar Chart", "📈 Line Chart", "📋 Data Table"])

# ───────────────────────────────────────────────────────────────────────────────
# TAB 1 – BAR CHART
# ───────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown(f"### Total Job Applications by Category (Top {top_n}, Descending Order)") #top_n(line 81) - chart setting sidebar - max 40 categories.
    st.caption("Bars are ordered from highest to lowest total applications among high-demand / low-application categories.")

    if filtered_sorted.empty:
        st.warning("No categories match your current filters. Try loosening the sliders.")
    else:
        fig, ax = plt.subplots(figsize=(14, max(6, top_n * 0.5))) #Top_n - Chart setting slider
        palette = sns.color_palette(bar_palette, len(filtered_sorted))

        bars = sns.barplot(
            data=filtered_sorted,
            x="total_applications",
            y="label",
            palette=palette,
            order=filtered_sorted["label"],
            ax=ax,
            orient="h",
        )

        # Add value labels inside / outside bars
        for bar, val in zip(ax.patches, filtered_sorted["total_applications"]):
            width = bar.get_width()
            ax.text(
                width + ax.get_xlim()[1] * 0.005,
                bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}",
                va="center", ha="left", fontsize=8.5, color="#333",
            )

        ax.set_xlabel("Total Applications", fontsize=12, labelpad=8)
        ax.set_ylabel("")
        ax.set_title(
            f"Top {top_n} High-Demand / Low-Application Categories\n"
            f"(Postings > {posting_pct}th pct  ·  Avg Apps < {app_pct}th pct)",
            fontsize=13, fontweight="bold", pad=14,
        )
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="y", labelsize=9)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

# ───────────────────────────────────────────────────────────────────────────────
# TAB 2 – LINE CHART
# ───────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"### Applications vs Postings – Trend Across Top {top_n} Categories")
    st.caption(
        "Line plots show total applications (solid) and total postings (dashed) "
        "across categories sorted by total applications (descending). "
        "A large gap between the two lines highlights the demand-supply mismatch."
    )

    if filtered_sorted.empty:
        st.warning("No categories match your current filters. Try loosening the sliders.")
    else:
        # Rank for x-axis
        plot_df = filtered_sorted.reset_index(drop=True) #Drop index column for line plot
        plot_df["rank"] = range(1, len(plot_df) + 1) #Similar to range(0, length of filtered sorted)

        fig2, ax2 = plt.subplots(figsize=(14, 5.5))

        sns.lineplot(
            data=plot_df, x="rank", y="total_applications",
            marker="o", color=line_palette, linewidth=2.5,
            markersize=6, label="Total Applications", ax=ax2,
        )
        sns.lineplot(
            data=plot_df, x="rank", y="total_postings",
            marker="s", linestyle="--", color="steelblue", linewidth=2,
            markersize=5, label="Total Postings", ax=ax2,
        )

        # Fill gap between lines
        ax2.fill_between(
            plot_df["rank"],
            plot_df["total_applications"],
            plot_df["total_postings"],
            alpha=0.10, color="gray",
        )

        # Annotate max gap
        plot_df["gap"] = plot_df["total_postings"] - plot_df["total_applications"]
        max_gap_row = plot_df.loc[plot_df["gap"].idxmax()]
        ax2.annotate(
            f"  Largest gap\n  {int(max_gap_row['gap']):,} unfilled",
            xy=(max_gap_row["rank"], max_gap_row["total_applications"]),
            xytext=(max_gap_row["rank"] + 0.5, max_gap_row["total_applications"] + max_gap_row["gap"] * 0.5),
            fontsize=8.5, color="#c0392b",
            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.2),
        )

        ax2.set_xlabel("Category Rank (by Total Applications, 1 = Highest)", fontsize=11)
        ax2.set_ylabel("Count", fontsize=11)
        ax2.set_title(
            f"Applications vs Postings for Top {top_n} High-Demand / Low-Application Categories",
            fontsize=13, fontweight="bold",
        )
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{int(y):,}"))
        ax2.set_xticks(plot_df["rank"])
        ax2.set_xticklabels(plot_df["rank"], fontsize=8)
        ax2.legend(fontsize=10)
        ax2.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

        st.markdown("#### Category Names by Rank")
        rank_table = plot_df[["rank", "label", "total_postings", "total_applications", "avg_applications"]].copy()
        rank_table.columns = ["Rank", "Category", "Total Postings", "Total Applications", "Avg Applications"]
        rank_table["Avg Applications"] = rank_table["Avg Applications"].round(2)
        st.dataframe(rank_table, use_container_width=True, hide_index=True)

# ───────────────────────────────────────────────────────────────────────────────
# TAB 3 – DATA TABLE
# ───────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Full Filtered Dataset")
    st.caption("All categories that satisfy the high-demand / low-application criteria, sorted by total applications (descending).")

    display_df = filtered.sort_values("total_applications", ascending=False).reset_index(drop=True)
    display_df.index += 1
    display_df.columns = ["Category", "Total Postings", "Total Applications", "Avg Applications", "Total Views"]
    display_df["Avg Applications"] = display_df["Avg Applications"].round(3)

    st.dataframe(
        display_df.style.background_gradient(subset=["Total Postings", "Total Applications"], cmap="coolwarm"),
        width='stretch',
        height=500,
    )

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️  Download CSV",
        data=csv,
        file_name="sg_high_demand_low_apps.csv",
        mime="text/csv",
    )

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Analysis: High demand = total postings above the chosen percentile | "
    "Low applications = average applications below the chosen percentile. "
    "Data sourced from the SG Job Market cleaned dataset."
)