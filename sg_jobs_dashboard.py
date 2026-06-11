import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ── Page config — must be the very first Streamlit call ───────────────────────
st.set_page_config(
    page_title="SG Jobs Market Dashboard",
    page_icon="🇸🇬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.metric-card {
    background: linear-gradient(135deg, #1e2130 0%, #252840 100%);
    border: 1px solid #2e3250; border-radius: 16px;
    padding: 24px 28px; text-align: center;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}
.metric-value {
    font-family: 'DM Serif Display', serif; font-size: 2.4rem;
    color: #7c9ef5; line-height: 1; margin-bottom: 6px;
}
.metric-label {
    font-size: 0.78rem; color: #8892b0;
    text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600;
}
.section-header {
    font-family: 'DM Serif Display', serif; font-size: 1.5rem;
    color: #e2e8f0; border-left: 4px solid #7c9ef5;
    padding-left: 14px; margin: 32px 0 18px;
}
</style>
""", unsafe_allow_html=True)


# ── Data loader ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data(source):
    df = pd.read_csv(source)
    df_exp = df.copy()
    df_exp["categories"] = df_exp["categories"].str.split(",")
    df_exp = df_exp.explode("categories")
    df_exp["categories"] = df_exp["categories"].str.strip()
    return df, df_exp


# ── Step 1: Get the data — everything else is inside this function ────────────
def run_dashboard(df):
    """Render the full dashboard. Only called once df is confirmed not None."""

    PALETTE = px.colors.qualitative.Plotly
    CHART_LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#c9d1e0"),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#c9d1e0"),
    )

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🇸🇬 SG Jobs Dashboard")
        st.markdown("*Singapore Job Market Analysis*")
        st.divider()

        all_cats = sorted(df["categories"].dropna().unique())
        selected_cats = st.multiselect("Filter by Category", options=all_cats,
                                       default=[], placeholder="All categories")

        all_emp = sorted(df["employmentTypes"].dropna().unique())
        selected_emp = st.multiselect("Employment Type", options=all_emp,
                                      default=[], placeholder="All types")

        all_levels = sorted(df["positionLevels"].dropna().unique())
        selected_levels = st.multiselect("Position Level", options=all_levels,
                                         default=[], placeholder="All levels")

        salary_min = int(df["salary_minimum"].min())
        salary_max = min(int(df["salary_maximum"].max()), 30000)
        salary_range = st.slider("Average Salary (SGD)",
                                 min_value=salary_min, max_value=salary_max,
                                 value=(salary_min, 15000), step=500)
        st.divider()
        st.caption("Data: MyCareersFuture SG")

    # ── Apply filters ─────────────────────────────────────────────────────────
    mask = df["average_salary"].between(salary_range[0], salary_range[1])
    if selected_cats:
        mask &= df["categories"].isin(selected_cats)
    if selected_emp:
        mask &= df["employmentTypes"].isin(selected_emp)
    if selected_levels:
        mask &= df["positionLevels"].isin(selected_levels)
    dff = df[mask]

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        "<p style='color:#8892b0;margin-top:-12px;'>MyCareersFuture data · 43 job categories</p>",
        unsafe_allow_html=True,
    )

    # ── KPI cards ─────────────────────────────────────────────────────────────
    total_postings  = dff["metadata_jobPostId"].nunique()
    total_apps      = dff["metadata_totalNumberJobApplication"].sum()
    avg_salary      = dff["average_salary"].mean()
    total_vacancies = dff["numberOfVacancies"].sum()
    total_views     = dff["metadata_totalNumberOfView"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, label in [
        (c1, f"{total_postings:,}",   "Job Postings"),
        (c2, f"{total_apps:,}",       "Total Applications"),
        (c3, f"S${avg_salary:,.0f}",  "Avg Monthly Salary"),
        (c4, f"{total_vacancies:,}",  "Total Vacancies"),
        (c5, f"{total_views:,}",      "Total Views"),
    ]:
        col.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value">{val}</div>'
            f'<div class="metric-label">{label}</div>'
            f'</div>', unsafe_allow_html=True,
        )

    # ── Row 1: Applications & Salary ──────────────────────────────────────────
    st.markdown('<div class="section-header">Applications & Salary by Category</div>',
                unsafe_allow_html=True)
    col_l, col_r = st.columns([3, 2])

    with col_l:
        cat_apps = (dff.groupby("categories", as_index=False)
                    ["metadata_totalNumberJobApplication"].sum()
                    .sort_values("metadata_totalNumberJobApplication", ascending=True).tail(20))
        fig1 = px.bar(cat_apps, x="metadata_totalNumberJobApplication", y="categories",
                      orientation="h", title="Top 20 Categories by Total Applications",
                      color="metadata_totalNumberJobApplication", color_continuous_scale="Blues",
                      labels={"metadata_totalNumberJobApplication": "Applications", "categories": ""})
        fig1.update_layout(**CHART_LAYOUT, coloraxis_showscale=False, height=520)
        fig1.update_traces(marker_line_width=0)
        st.plotly_chart(fig1, use_container_width=True)

    with col_r:
        cat_sal = (dff.groupby("categories", as_index=False)["average_salary"].mean()
                   .sort_values("average_salary", ascending=False).head(15))
        fig2 = px.bar(cat_sal, x="categories", y="average_salary",
                      title="Top 15 Categories by Avg Salary",
                      color="average_salary", color_continuous_scale="Teal",
                      labels={"average_salary": "Avg Salary (SGD)", "categories": ""})
        fig2.update_layout(**CHART_LAYOUT, coloraxis_showscale=False, height=520, xaxis_tickangle=-45)
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Employment / Level / Status ────────────────────────────────────
    st.markdown('<div class="section-header">Employment Type & Position Level</div>',
                unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        emp_counts = dff["employmentTypes"].value_counts().reset_index()
        emp_counts.columns = ["type", "count"]
        fig3 = px.pie(emp_counts, names="type", values="count", title="Employment Types",
                      color_discrete_sequence=PALETTE, hole=0.45)
        fig3.update_layout(**CHART_LAYOUT, height=380)
        fig3.update_traces(textfont_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        lvl_counts = dff["positionLevels"].value_counts().reset_index()
        lvl_counts.columns = ["level", "count"]
        fig4 = px.bar(lvl_counts.sort_values("count"), x="count", y="level",
                      orientation="h", title="Position Levels",
                      color="count", color_continuous_scale="Purples",
                      labels={"count": "Postings", "level": ""})
        fig4.update_layout(**CHART_LAYOUT, coloraxis_showscale=False, height=380)
        fig4.update_traces(marker_line_width=0)
        st.plotly_chart(fig4, use_container_width=True)

    with col_c:
        status_counts = dff["status_jobStatus"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig5 = px.pie(status_counts, names="status", values="count",
                      title="Job Status Distribution", hole=0.45, color="status",
                      color_discrete_map={"Open": "#4ade80", "Closed": "#f87171", "Re-Open": "#facc15"})
        fig5.update_layout(**CHART_LAYOUT, height=380)
        fig5.update_traces(textfont_color="white")
        st.plotly_chart(fig5, use_container_width=True)

    # ── Row 3: Salary dist + Scatter ─────────────────────────────────────────
    st.markdown('<div class="section-header">Salary Distribution & Job Competition</div>',
                unsafe_allow_html=True)
    col_d, col_e = st.columns(2)

    with col_d:
        fig6 = px.histogram(dff[dff["average_salary"] > 0], x="average_salary", nbins=60,
                            title="Average Salary Distribution",
                            color_discrete_sequence=["#7c9ef5"],
                            labels={"average_salary": "Average Salary (SGD)"})
        fig6.update_layout(**CHART_LAYOUT, height=360)
        fig6.update_traces(marker_line_width=0)
        st.plotly_chart(fig6, use_container_width=True)

    with col_e:
        scatter_df = (dff.groupby("categories", as_index=False)
                      .agg(avg_salary=("average_salary", "mean"),
                           total_apps=("metadata_totalNumberJobApplication", "sum"),
                           total_postings=("metadata_jobPostId", "nunique")))
        fig7 = px.scatter(scatter_df, x="avg_salary", y="total_apps",
                          size="total_postings", color="categories",
                          hover_name="categories",
                          title="Salary vs Applications (bubble = postings)",
                          labels={"avg_salary": "Avg Salary (SGD)", "total_apps": "Total Applications"},
                          color_discrete_sequence=PALETTE)
        fig7.update_layout(**CHART_LAYOUT, height=360, showlegend=False)
        st.plotly_chart(fig7, use_container_width=True)

    # ── Row 4: Experience line + Box ─────────────────────────────────────────
    st.markdown('<div class="section-header">Experience vs Salary Insights</div>',
                unsafe_allow_html=True)
    col_f, col_g = st.columns(2)

    with col_f:
        exp_sal = (dff[dff["minimumYearsExperience"] <= 15]
                   .groupby("minimumYearsExperience", as_index=False)["average_salary"].mean())
        fig8 = px.line(exp_sal, x="minimumYearsExperience", y="average_salary",
                       title="Avg Salary by Minimum Years of Experience", markers=True,
                       color_discrete_sequence=["#7c9ef5"],
                       labels={"minimumYearsExperience": "Min Years Experience",
                               "average_salary": "Avg Salary (SGD)"})
        fig8.update_layout(**CHART_LAYOUT, height=360)
        st.plotly_chart(fig8, use_container_width=True)

    with col_g:
        top10_cats = (dff.groupby("categories")["metadata_totalNumberJobApplication"]
                      .sum().nlargest(10).index)
        fig9 = px.box(dff[dff["categories"].isin(top10_cats)],
                      x="categories", y="average_salary",
                      title="Salary Range – Top 10 Categories",
                      color="categories", color_discrete_sequence=PALETTE,
                      labels={"categories": "", "average_salary": "Salary (SGD)"})
        fig9.update_layout(**CHART_LAYOUT, height=360, showlegend=False, xaxis_tickangle=-30)
        st.plotly_chart(fig9, use_container_width=True)

    # ── Row 5: Top companies ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">Top Hiring Companies</div>', unsafe_allow_html=True)
    col_h, col_i = st.columns(2)

    with col_h:
        top_co_apps = (dff.groupby("postedCompany_name", as_index=False)
                       ["metadata_totalNumberJobApplication"].sum()
                       .sort_values("metadata_totalNumberJobApplication", ascending=True).tail(15))
        fig10 = px.bar(top_co_apps, x="metadata_totalNumberJobApplication", y="postedCompany_name",
                       orientation="h", title="Top 15 Companies by Applications Received",
                       color="metadata_totalNumberJobApplication", color_continuous_scale="Blues",
                       labels={"metadata_totalNumberJobApplication": "Applications", "postedCompany_name": ""})
        fig10.update_layout(**CHART_LAYOUT, coloraxis_showscale=False, height=460)
        fig10.update_traces(marker_line_width=0)
        st.plotly_chart(fig10, use_container_width=True)

    with col_i:
        top_co_post = (dff.groupby("postedCompany_name")["metadata_jobPostId"]
                       .nunique().reset_index()
                       .rename(columns={"metadata_jobPostId": "postings"})
                       .sort_values("postings", ascending=True).tail(15))
        fig11 = px.bar(top_co_post, x="postings", y="postedCompany_name",
                       orientation="h", title="Top 15 Companies by Number of Job Postings",
                       color="postings", color_continuous_scale="Teal",
                       labels={"postings": "Postings", "postedCompany_name": ""})
        fig11.update_layout(**CHART_LAYOUT, coloraxis_showscale=False, height=460)
        fig11.update_traces(marker_line_width=0)
        st.plotly_chart(fig11, use_container_width=True)

    # ── Data Explorer ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Data Explorer</div>', unsafe_allow_html=True)
    with st.expander("Browse filtered records", expanded=False):
        display_cols = ["categories", "title", "postedCompany_name", "employmentTypes",
                        "positionLevels", "average_salary", "numberOfVacancies",
                        "metadata_totalNumberJobApplication", "status_jobStatus"]
        result = dff[display_cols].drop_duplicates().reset_index(drop=True)
        st.dataframe(result, use_container_width=True, height=400)
        st.caption(f"{len(result):,} records shown after filters.")

    # ── Footer ────────────────────────────────────────────────────────────────
    st.divider()
    st.markdown(
        "<p style='text-align:center;color:#4a5568;font-size:0.8rem;'>"
        "SG Job Market Dashboard · Built with Streamlit & Plotly · Data: MyCareersFuture</p>",
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
# MAIN — data gate: nothing runs until df is confirmed loaded
# ═════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h1 style='font-family:DM Serif Display,serif;color:#e2e8f0;margin-bottom:4px;'>"
    "🇸🇬 Singapore Job Market Dashboard</h1>",
    unsafe_allow_html=True,
)

LOCAL_FILE = "sg_job_data_cleaned.csv"

# Always show uploader so users can refresh with a new file
uploaded = st.file_uploader(
    "Upload CSV (or place it in the same folder as this script)",
    type="csv",
    label_visibility="collapsed",
)

if uploaded is not None:
    # User uploaded a file — use it
    _, df = load_data(uploaded)
    run_dashboard(df)

elif os.path.exists(LOCAL_FILE):
    # CSV found locally next to the script — use it silently
    _, df = load_data(LOCAL_FILE)
    run_dashboard(df)

else:
    # No file available — ask for upload, do NOT call run_dashboard
    st.info("👆 Please upload `sg_job_data_cleaned.csv` to load the dashboard.")
    st.markdown(
        "**Tip:** You can also place the CSV in the same folder as `sg_jobs_dashboard.py` "
        "and it will load automatically.",
    )