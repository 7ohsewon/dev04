import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="4주기 대학현황지표 대시보드",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #F1F5F9; }
    [data-testid="stSidebar"] { background: #1E293B; }
    [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    .main-header {
        background: linear-gradient(135deg, #1E3A5F 0%, #2563EB 100%);
        color: white; padding: 24px 32px; border-radius: 14px; margin-bottom: 24px;
    }
    .main-header h1 { margin: 0; font-size: 1.7rem; }
    .main-header p { margin: 6px 0 0; opacity: 0.85; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# ── Color System ──────────────────────────────────────────
COLOR_MAP = {
    "국립": "#2563EB",
    "사립": "#EA580C",
    "국립대법인": "#0EA5E9",
    "공립": "#10B981",
}

# ── Data Loader ───────────────────────────────────────────
@st.cache_data(ttl=0)
def load_data():
    csv_path = "4주기 2025년도 대학현황지표.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 열 이름 정리
    df.columns = df.columns.str.strip()

    return df

# Load data
try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 로드 실패: {str(e)}")
    st.stop()

# ── Header ────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎓 4주기 대학현황지표 대시보드</h1>
    <p>대학 교육역량 종합진단 평가 지표</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar: Filters ──────────────────────────────────────
st.sidebar.header("📊 필터")

# Get actual column names
col1_name = df.columns[0]  # 학교명
col2_name = df.columns[1]  # 설립구분
col3_name = df.columns[2]  # 지역

# University selection
universities = sorted(df[col1_name].unique())
selected_univs = st.sidebar.multiselect(
    "대학 선택",
    universities,
    default=universities[:5] if len(universities) > 5 else universities
)

if not selected_univs:
    st.warning("최소 1개 이상의 대학을 선택해주세요.")
    st.stop()

# Filter data
df_filtered = df[df[col1_name].isin(selected_univs)].copy()

# ── Main Content ──────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📚 선택된 대학 수", len(selected_univs))

with col2:
    st.metric("🏛️ 설립구분 수", df_filtered[col2_name].nunique())

with col3:
    st.metric("📍 지역 수", df_filtered[col3_name].nunique())

st.divider()

# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 지표 비교", "📋 상세정보", "🔍 통계"])

with tab1:
    st.subheader("지표별 비교")

    # Get numeric columns (exclude first 3: 학교명, 설립구분, 지역)
    numeric_cols = df_filtered.select_dtypes(include=[np.number]).columns.tolist()

    if numeric_cols:
        selected_metric = st.selectbox(
            "비교할 지표 선택",
            numeric_cols,
            index=0
        )

        # Prepare data for chart
        chart_data = df_filtered[[col1_name, selected_metric]].copy()
        chart_data = chart_data.dropna(subset=[selected_metric])
        chart_data = chart_data.sort_values(selected_metric, ascending=False)

        if not chart_data.empty:
            fig = px.bar(
                chart_data,
                x=col1_name,
                y=selected_metric,
                title=f"📊 {selected_metric} 비교",
                labels={col1_name: "대학", selected_metric: selected_metric},
                color=selected_metric,
                color_continuous_scale="Viridis"
            )
            fig.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("해당 지표에 대한 데이터가 없습니다.")
    else:
        st.info("비교 가능한 수치 지표가 없습니다.")

with tab2:
    st.subheader("선택된 대학의 상세정보")

    # Display table
    display_cols = [col1_name, col2_name, col3_name] + numeric_cols[:10]
    display_df = df_filtered[display_cols].copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        height=500
    )

    # Download option
    csv = display_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSV 다운로드",
        data=csv,
        file_name="대학현황지표.csv",
        mime="text/csv"
    )

with tab3:
    st.subheader("통계")

    if numeric_cols:
        selected_stat_metric = st.selectbox(
            "통계를 확인할 지표",
            numeric_cols,
            index=0,
            key="stat_metric"
        )

        stat_data = df_filtered[selected_stat_metric].dropna()

        if not stat_data.empty:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("평균", f"{stat_data.mean():.2f}")
            with col2:
                st.metric("중앙값", f"{stat_data.median():.2f}")
            with col3:
                st.metric("최대값", f"{stat_data.max():.2f}")
            with col4:
                st.metric("최소값", f"{stat_data.min():.2f}")

            # Distribution chart
            fig_hist = px.histogram(
                df_filtered,
                x=selected_stat_metric,
                nbins=30,
                title=f"📊 {selected_stat_metric} 분포",
                labels={selected_stat_metric: selected_stat_metric},
                color_discrete_sequence=["#3B82F6"]
            )
            fig_hist.update_layout(height=400)
            st.plotly_chart(fig_hist, use_container_width=True)

# ── Footer ────────────────────────────────────────────────
st.divider()
st.caption("📊 4주기 2025년도 대학현황지표 | 대학 교육역량 종합진단")
