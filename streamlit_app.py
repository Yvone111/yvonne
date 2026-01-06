import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import io
import warnings
from datetime import datetime, timedelta
import sys

# 添加自定义模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

warnings.filterwarnings('ignore')

# 设置页面配置
st.set_page_config(
    page_title="营养顾问绩效评估系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 使用单行字符串替代多行字符串避免问题
st.markdown(
    '<style>.main .block-container {padding-top: 1rem; padding-bottom: 1rem;} h1 {font-size: 1.8rem !important;} h2 {font-size: 1.5rem !important;} h3 {font-size: 1.3rem !important;} .stMetric {font-size: 0.9rem !important;} .css-1d391kg {font-size: 0.9rem;} div[data-testid="stMetricValue"] {font-size: 1.1rem !important;} .scrollable-table {max-height: 600px; overflow-y: auto; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.25rem; padding: 10px;}</style>',
    unsafe_allow_html=True)


class NutritionAdviserDashboard:
    def __init__(self):
        """营养顾问绩效评估仪表板 - 云端部署版本"""
        self.monthly_data = {}

    def load_data_from_upload(self, uploaded_files):
        """从上传的文件加载数据"""
        for uploaded_file in uploaded_files:
            try:
                filename = uploaded_file.name
                month_key = self.extract_month_from_filename(filename)
                df = pd.read_excel(uploaded_file)
                df['月份'] = month_key
                df['日期'] = datetime.now()

                self.monthly_data[month_key] = {
                    'data': df,
                    'date': datetime.now(),
                    'file_path': f"上传文件: {filename}"
                }

                st.sidebar.success(f"✅ 已加载: {month_key} (共{len(df)}条记录)")
            except Exception as e:
                st.sidebar.error(f"❌ 处理文件 {uploaded_file.name} 时出错: {str(e)}")

    def extract_month_from_filename(self, filename):
        """从文件名提取月份信息"""
        if "利润模型评估报告_原始收益值_" in filename:
            date_str = filename.replace("利润模型评估报告_原始收益值_", "").replace(".xlsx", "")
        elif "利润模型评估报告_" in filename:
            date_str = filename.replace("利润模型评估报告_", "").replace(".xlsx", "")
        else:
            date_str = filename.replace(".xlsx", "")

        try:
            if len(date_str) == 6 and date_str.isdigit():
                file_date = datetime.strptime(date_str, "%Y%m")
                return file_date.strftime("%Y年%m月")
            elif len(date_str) == 8 and date_str.isdigit():
                file_date = datetime.strptime(date_str, "%Y%m%d")
                return file_date.strftime("%Y年%m月")
        except ValueError:
            pass

        return filename.replace(".xlsx", "")

    def get_available_months(self):
        """获取可用的月份列表"""
        if not self.monthly_data:
            return []
        return sorted(self.monthly_data.keys(),
                      key=lambda x: self.monthly_data[x]['date'],
                      reverse=True)

    def get_month_data(self, month):
        """获取指定月份的数据"""
        return self.monthly_data.get(month, {}).get('data', pd.DataFrame())

    def get_previous_month(self, current_month):
        """获取上一个月份的数据"""
        months = self.get_available_months()
        if not months or current_month not in months:
            return None
        current_index = months.index(current_month)
        if current_index < len(months) - 1:
            return months[current_index + 1]
        return None

    def create_member_value_analysis(self, selected_month):
        """创建会员价值贡献分析"""
        st.header(f"📈 会员价值贡献分析 - {selected_month}")

        # 获取当月数据
        current_month_data = self.get_month_data(selected_month)
        if current_month_data.empty or '会员价值贡献' not in current_month_data.columns or '大区' not in current_month_data.columns:
            st.warning("当月数据中没有会员价值贡献或大区信息")
            return

        # 功能1: 各区域会员价值贡献总量柱状图
        st.subheader("1. 各区域会员价值贡献总量")

        # 计算各区域会员价值贡献总量
        region_member_value = current_month_data.groupby('大区')['会员价值贡献'].sum().reset_index()
        region_member_value = region_member_value.sort_values('会员价值贡献', ascending=True)

        # 创建柱状图
        fig1 = px.bar(
            region_member_value,
            y='大区',
            x='会员价值贡献',
            orientation='h',
            title=f"{selected_month} 各区域会员价值贡献总量",
            color='会员价值贡献',
            color_continuous_scale='Viridis',
            text_auto='.0f'
        )
        fig1.update_layout(
            yaxis_title="大区",
            xaxis_title="会员价值贡献总量（元）",
            height=500
        )
        st.plotly_chart(fig1, use_container_width=True)

        # 显示详细数据
        st.subheader("各区域会员价值贡献详细数据")

        # 计算各区域的统计指标
        region_stats = current_month_data.groupby('大区').agg({
            '会员价值贡献': ['sum', 'mean', 'count']
        }).round(0)

        region_stats.columns = ['贡献总量', '人均贡献', '顾问人数']
        region_stats = region_stats.reset_index()
        region_stats = region_stats.sort_values('贡献总量', ascending=False)

        # 添加排名
        region_stats['排名'] = range(1, len(region_stats) + 1)
        region_stats = region_stats[['排名', '大区', '贡献总量', '人均贡献', '顾问人数']]

        # 格式化显示
        region_stats['贡献总量'] = region_stats['贡献总量'].apply(lambda x: f"¥{x:,.0f}")
        region_stats['人均贡献'] = region_stats['人均贡献'].apply(lambda x: f"¥{x:,.0f}")

        st.dataframe(region_stats, use_container_width=True)

        # 功能2: 当月与上月各区域会员价值贡献对比
        st.subheader("2. 当月与上月各区域会员价值贡献对比")

        # 获取上月数据
        previous_month = self.get_previous_month(selected_month)

        if previous_month:
            previous_month_data = self.get_month_data(previous_month)

            if not previous_month_data.empty and '会员价值贡献' in previous_month_data.columns and '大区' in previous_month_data.columns:
                # 计算当月各区域会员价值贡献总量
                current_summary = current_month_data.groupby('大区')['会员价值贡献'].sum().reset_index()
                current_summary.columns = ['大区', '当月贡献']

                # 计算上月各区域会员价值贡献总量
                previous_summary = previous_month_data.groupby('大区')['会员价值贡献'].sum().reset_index()
                previous_summary.columns = ['大区', '上月贡献']

                # 合并数据
                comparison = pd.merge(current_summary, previous_summary, on='大区', how='outer')
                comparison = comparison.fillna(0)

                # 计算变化量和变化百分比
                comparison['变化量'] = comparison['当月贡献'] - comparison['上月贡献']
                comparison['变化百分比'] = (comparison['变化量'] / comparison['上月贡献'] * 100).round(1)
                comparison = comparison.fillna(0)

                # 创建变化量柱状图
                fig2 = px.bar(
                    comparison,
                    x='大区',
                    y='变化量',
                    title=f"{selected_month} 与 {previous_month} 各区域会员价值贡献变化量",
                    color='变化量',
                    color_continuous_scale='RdYlGn',
                    text_auto='+.0f'
                )
                fig2.update_layout(
                    xaxis_title="大区",
                    yaxis_title="变化量（元）",
                    height=400
                )
                fig2.update_traces(texttemplate='%{y:+,.0f}元')
                st.plotly_chart(fig2, use_container_width=True)

                # 创建变化百分比柱状图
                fig3 = px.bar(
                    comparison,
                    x='大区',
                    y='变化百分比',
                    title=f"{selected_month} 与 {previous_month} 各区域会员价值贡献变化百分比",
                    color='变化百分比',
                    color_continuous_scale='RdYlGn',
                    text_auto='+.1f'
                )
                fig3.update_layout(
                    xaxis_title="大区",
                    yaxis_title="变化百分比 (%)",
                    height=400
                )
                fig3.update_traces(texttemplate='%{y:+.1f}%')
                st.plotly_chart(fig3, use_container_width=True)

                # 创建对比折线图
                st.subheader("各区域会员价值贡献趋势对比")

                # 准备数据
                trend_data = []
                for _, row in comparison.iterrows():
                    trend_data.append({
                        '大区': row['大区'],
                        '贡献值': row['上月贡献'],
                        '月份': previous_month
                    })
                    trend_data.append({
                        '大区': row['大区'],
                        '贡献值': row['当月贡献'],
                        '月份': selected_month
                    })

                trend_df = pd.DataFrame(trend_data)

                # 创建折线图
                fig4 = px.line(
                    trend_df,
                    x='月份',
                    y='贡献值',
                    color='大区',
                    markers=True,
                    title=f"各区域会员价值贡献趋势对比 ({previous_month} → {selected_month})",
                    line_shape='spline'
                )
                fig4.update_layout(
                    xaxis_title="月份",
                    yaxis_title="会员价值贡献（元）",
                    height=500,
                    legend_title="大区"
                )
                st.plotly_chart(fig4, use_container_width=True)

                # 显示详细对比数据
                st.subheader("详细对比数据")

                # 格式化显示
                display_comparison = comparison.copy()
                display_comparison['当月贡献'] = display_comparison['当月贡献'].apply(lambda x: f"¥{x:,.0f}")
                display_comparison['上月贡献'] = display_comparison['上月贡献'].apply(lambda x: f"¥{x:,.0f}")
                display_comparison['变化量'] = display_comparison['变化量'].apply(lambda x: f"¥{x:+,.0f}")
                display_comparison['变化百分比'] = display_comparison['变化百分比'].apply(lambda x: f"{x:+.1f}%")

                # 添加颜色标记函数
                def color_style(val):
                    if isinstance(val, str):
                        if '¥+' in val or '¥0' in val:
                            return 'color: green; font-weight: bold'
                        elif '¥-' in val:
                            return 'color: red; font-weight: bold'
                    if isinstance(val, str) and '%' in val:
                        try:
                            num = float(val.replace('%', '').replace('+', ''))
                            if num > 0:
                                return 'color: green; font-weight: bold'
                            elif num < 0:
                                return 'color: red; font-weight: bold'
                        except:
                            pass
                    return ''

                # 应用样式
                styled_df = display_comparison.style.applymap(color_style, subset=['变化量', '变化百分比'])
                st.dataframe(styled_df, use_container_width=True)

                # 显示关键发现
                st.subheader("💡 关键发现")

                # 找出增长最快和下降最多的区域
                if not comparison.empty:
                    # 增长最快的区域
                    top_growth = comparison.nlargest(1, '变化百分比')
                    if not top_growth.empty:
                        top_region = top_growth.iloc[0]['大区']
                        top_growth_pct = top_growth.iloc[0]['变化百分比']
                        top_growth_val = top_growth.iloc[0]['变化量']

                        st.success(
                            f"**增长最快**: {top_region} 区域会员价值贡献增长 {top_growth_pct:.1f}% (¥{top_growth_val:+,.0f})")

                    # 下降最多的区域
                    bottom_growth = comparison.nsmallest(1, '变化百分比')
                    if not bottom_growth.empty and bottom_growth.iloc[0]['变化百分比'] < 0:
                        bottom_region = bottom_growth.iloc[0]['大区']
                        bottom_growth_pct = bottom_growth.iloc[0]['变化百分比']
                        bottom_growth_val = bottom_growth.iloc[0]['变化量']

                        st.error(
                            f"**需关注**: {bottom_region} 区域会员价值贡献下降 {abs(bottom_growth_pct):.1f}% (¥{bottom_growth_val:+,.0f})")

                    # 计算总体变化
                    total_current = current_summary['当月贡献'].sum()
                    total_previous = previous_summary['上月贡献'].sum()
                    total_change = total_current - total_previous
                    total_change_pct = (total_change / total_previous * 100) if total_previous != 0 else 0

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("当月总贡献", f"¥{total_current:,.0f}")
                    with col2:
                        st.metric("上月总贡献", f"¥{total_previous:,.0f}")
                    with col3:
                        st.metric("总体变化", f"{total_change_pct:+.1f}%", f"¥{total_change:+,.0f}")
            else:
                st.warning(f"上月({previous_month})数据中没有会员价值贡献或大区信息")
        else:
            st.info("没有上月数据可用于对比分析")

    @st.cache_data(ttl=3600, show_spinner=False)
    def process_data_for_charts(_self, df, chart_type):
        """缓存数据处理函数"""
        if df.empty:
            return df

        if chart_type == "profit_distribution":
            if '最终收益值' not in df.columns:
                return pd.DataFrame()

            profit_bins = [-float('inf'), 0, 10000, 50000, 100000, 200000, float('inf')]
            profit_labels = ['亏损(<0)', '低收益(0-1万)', '中低收益(1-5万)',
                             '中收益(5-10万)', '中高收益(10-20万)', '高收益(>20万)']

            df_copy = df.copy()
            df_copy['收益分段'] = pd.cut(df_copy['最终收益值'], bins=profit_bins, labels=profit_labels)
            return df_copy['收益分段'].value_counts().reindex(profit_labels)

        return df

    def create_overview_dashboard(self, selected_month):
        """创建概览仪表板"""
        st.header(f"📊 营养顾问绩效评估概览 - {selected_month}")
        df = self.get_month_data(selected_month)

        if df.empty:
            st.warning(f"没有找到 {selected_month} 的数据")
            return

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_advisers = len(df)
            st.metric("总评估人数", f"{total_advisers}人")
        with col2:
            avg_profit = df['最终收益值'].mean() if '最终收益值' in df.columns else 0
            st.metric("平均收益", f"¥{avg_profit:,.0f}")
        with col3:
            total_profit = df['最终收益值'].sum() if '最终收益值' in df.columns else 0
            st.metric("总收益", f"¥{total_profit:,.0f}")
        with col4:
            if '最终收益值' in df.columns and len(df) > 0:
                threshold = df['最终收益值'].quantile(0.8)
                high_performers = len(df[df['最终收益值'] >= threshold])
                percentage = (high_performers / len(df)) * 100
                st.metric("高绩效顾问比例", f"{percentage:.1f}%")
            else:
                st.metric("高绩效顾问比例", "0%")

        col1, col2 = st.columns(2)
        with col1:
            self.create_profit_distribution_chart(df, selected_month)
        with col2:
            self.create_adviser_type_chart(df, selected_month)

        col1, col2 = st.columns(2)
        with col1:
            self.create_region_analysis_chart(df, selected_month)
        with col2:
            if len(self.monthly_data) > 1:
                self.create_trend_analysis_chart(selected_month)
            else:
                st.info("需要多个月份数据才能显示趋势分析")

    def create_profit_distribution_chart(self, df, month):
        """创建收益分布图表"""
        st.subheader("📈 收益分布情况")

        if '最终收益值' not in df.columns or df.empty:
            st.warning("没有收益数据可显示")
            return

        distribution = self.process_data_for_charts(df, "profit_distribution")

        if distribution.empty:
            st.warning("无法生成收益分布图")
            return

        fig = px.pie(
            values=distribution.values,
            names=distribution.index,
            title=f"{month} 收益分布",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=False, height=400)

        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("最高收益", f"¥{df['最终收益值'].max():,.0f}")
        with col2:
            st.metric("中位数", f"¥{df['最终收益值'].median():,.0f}")
        with col3:
            st.metric("最低收益", f"¥{df['最终收益值'].min():,.0f}")

    def create_adviser_type_chart(self, df, month):
        """创建顾问类型分析图表"""
        st.subheader("👥 各类型顾问表现")

        if '顾问编制' not in df.columns or '最终收益值' not in df.columns:
            st.warning("缺少必要的数据列")
            return

        type_stats = df.groupby('顾问编制').agg({
            '最终收益值': ['count', 'mean', 'median', 'std']
        }).round(0)
        type_stats.columns = ['人数', '平均收益', '中位收益', '标准差']
        type_stats = type_stats.reset_index()

        fig = px.bar(
            type_stats,
            x='顾问编制',
            y='平均收益',
            title=f"{month} 各类型顾问平均收益",
            color='平均收益',
            color_continuous_scale='Viridis',
            text_auto='.0f'
        )
        fig.update_layout(
            xaxis_title="顾问类型",
            yaxis_title="平均收益（元）",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("各类型顾问销售利润分布")

        if '销售利润' not in df.columns:
            st.warning("没有销售利润数据")
            return

        sales_bins = [0, 20000, 50000, 100000, float('inf')]
        sales_labels = ['2万以下', '2-5万', '5-10万', '10万以上']

        df_copy = df.copy()
        df_copy['销售利润坎级'] = pd.cut(df_copy['销售利润'], bins=sales_bins, labels=sales_labels)
        sales_distribution = df_copy.groupby(['顾问编制', '销售利润坎级']).size().unstack(fill_value=0)

        if not sales_distribution.empty:
            self.create_stacked_bar_chart(sales_distribution, month)

    def create_stacked_bar_chart(self, sales_distribution, month):
        """创建堆叠条形图"""
        adviser_types = sales_distribution.index.tolist()
        sales_labels = sales_distribution.columns.tolist()
        fig = go.Figure()
        colors = ['#8dd3c7', '#ffffb4', '#bebadb', '#fb8072']

        for i, label in enumerate(sales_labels):
            y_data = sales_distribution[label]
            text_positions = []
            for value in y_data:
                if value == 0:
                    text_positions.append("")
                else:
                    text_positions.append(f"{int(value)}")

            fig.add_trace(go.Bar(
                name=label,
                x=adviser_types,
                y=y_data,
                text=text_positions,
                textposition='outside',
                textfont=dict(size=12, color='black'),
                marker_color=colors[i % len(colors)],
                hovertemplate=f"<b>{label}</b><br>顾问类型: %{x}<br>人数: %{y}<br><extra></extra>"
            ))

        fig.update_layout(
            title=dict(text=f"{month} 各类型顾问销售利润分布", font=dict(size=18)),
            xaxis=dict(title="顾问类型", title_font=dict(size=14), tickfont=dict(size=12)),
            yaxis=dict(title="人数", title_font=dict(size=14), tickfont=dict(size=12)),
            barmode='stack',
            height=500,
            showlegend=True,
            margin=dict(l=50, r=50, t=80, b=50),
        )

        max_value = sales_distribution.sum(axis=1).max()
        fig.update_yaxes(range=[0, max_value * 1.15])
        st.plotly_chart(fig, use_container_width=True)

    def create_region_analysis_chart(self, df, month):
        """创建大区分析图表"""
        st.subheader("🌍 大区绩效分析")

        if '大区' not in df.columns or '最终收益值' not in df.columns:
            st.warning("缺少大区数据")
            return

        region_stats = df.groupby('大区').agg({
            '最终收益值': ['mean', 'count']
        }).round(0)
        region_stats.columns = ['平均收益', '顾问人数']
        region_stats = region_stats.reset_index()

        if len(region_stats) == 0:
            st.warning("没有大区数据可显示")
            return

        region_stats = region_stats.sort_values('平均收益', ascending=True)

        fig = px.bar(
            region_stats,
            y='大区',
            x='平均收益',
            orientation='h',
            title=f"{month} 各区域绩效对比",
            color='平均收益',
            color_continuous_scale='RdYlGn',
            text_auto='.0f'
        )
        fig.update_layout(
            yaxis_title="大区",
            xaxis_title="平均收益（元）",
            height=400,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("区域表现分析")

        if len(region_stats) > 1:
            best_region = region_stats.loc[region_stats['平均收益'].idxmax()]
            worst_region = region_stats.loc[region_stats['平均收益'].idxmin()]

            col1, col2 = st.columns(2)
            with col1:
                st.success(f"🏆 最佳表现: {best_region['大区']}")
                st.metric("平均收益", f"¥{best_region['平均收益']:,.0f}")
                st.metric("顾问人数", f"{best_region['顾问人数']}人")
            with col2:
                st.error(f"📉 需改进: {worst_region['大区']}")
                st.metric("平均收益", f"¥{worst_region['平均收益']:,.0f}")
                st.metric("顾问人数", f"{worst_region['顾问人数']}人")

    def create_trend_analysis_chart(self, selected_month):
        """创建趋势分析图表"""
        st.subheader("📅 多月份趋势分析")

        if len(self.monthly_data) < 2:
            st.info("需要至少两个月份的数据才能显示趋势分析")
            return

        trend_data = []
        for month, data_info in self.monthly_data.items():
            df = data_info['data']
            if '最终收益值' in df.columns and '顾问编制' in df.columns:
                overall_avg = df['最终收益值'].mean()
                trend_data.append({
                    '月份': month,
                    '日期': data_info['date'],
                    '总体平均收益': overall_avg,
                })

        if not trend_data:
            st.warning("没有足够的数据进行趋势分析")
            return

        trend_df = pd.DataFrame(trend_data)
        trend_df = trend_df.sort_values('日期')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df['月份'],
            y=trend_df['总体平均收益'],
            mode='lines+markers',
            name='总体平均',
            line=dict(width=4)
        ))

        fig.update_layout(
            title="各月份收益趋势",
            xaxis_title="月份",
            yaxis_title="平均收益（元）",
            height=400,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    def create_performance_comparison(self, df, month):
        """创建前100名与后100名营养顾问的优劣势分析"""
        st.subheader("🏆 前100名 vs 后100名 营养顾问优劣势分析")

        if df.empty or '最终收益值' not in df.columns:
            st.warning("无法进行绩效对比分析")
            return

        # 检查数据量是否足够
        if len(df) < 200:
            st.warning(f"数据量不足（当前{len(df)}条记录），需要至少200条记录才能进行前100名与后100名对比分析")
            return

        # 获取前100名和后100名
        top_100 = df.nlargest(100, '最终收益值')
        bottom_100 = df.nsmallest(100, '最终收益值')

        # 计算各项指标的平均值
        comparison_data = {
            '指标': ['销售利润', '新客贡献', '会员价值贡献', '试饮获客贡献', 'A+B内码贡献', '总收益'],
            '前100名平均值': [
                top_100['销售利润'].mean() if '销售利润' in top_100.columns else 0,
                top_100['新客贡献'].mean() if '新客贡献' in top_100.columns else 0,
                top_100['会员价值贡献'].mean() if '会员价值贡献' in top_100.columns else 0,
                top_100['试饮获客贡献'].mean() if '试饮获客贡献' in top_100.columns else 0,
                top_100['A+B内码贡献'].mean() if 'A+B内码贡献' in top_100.columns else 0,
                top_100['总收益'].mean() if '总收益' in top_100.columns else 0
            ],
            '后100名平均值': [
                bottom_100['销售利润'].mean() if '销售利润' in bottom_100.columns else 0,
                bottom_100['新客贡献'].mean() if '新客贡献' in bottom_100.columns else 0,
                bottom_100['会员价值贡献'].mean() if '会员价值贡献' in bottom_100.columns else 0,
                bottom_100['试饮获客贡献'].mean() if '试饮获客贡献' in bottom_100.columns else 0,
                bottom_100['A+B内码贡献'].mean() if 'A+B内码贡献' in bottom_100.columns else 0,
                bottom_100['总收益'].mean() if '总收益' in bottom_100.columns else 0
            ],
            '全量平均值': [
                df['销售利润'].mean() if '销售利润' in df.columns else 0,
                df['新客贡献'].mean() if '新客贡献' in df.columns else 0,
                df['会员价值贡献'].mean() if '会员价值贡献' in df.columns else 0,
                df['试饮获客贡献'].mean() if '试饮获客贡献' in df.columns else 0,
                df['A+B内码贡献'].mean() if 'A+B内码贡献' in df.columns else 0,
                df['总收益'].mean() if '总收益' in df.columns else 0
            ]
        }

        comparison_df = pd.DataFrame(comparison_data)
        comparison_df['前100名优势百分比'] = (
                    (comparison_df['前100名平均值'] - comparison_df['后100名平均值']) / comparison_df[
                '后100名平均值'] * 100).round(1)
        comparison_df['前100名vs全量优势百分比'] = (
                    (comparison_df['前100名平均值'] - comparison_df['全量平均值']) / comparison_df[
                '全量平均值'] * 100).round(1)
        comparison_df = comparison_df.fillna(0)

        # 显示关键指标对比
        st.subheader("📊 关键指标对比")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("前100名平均收益", f"¥{top_100['最终收益值'].mean():,.0f}")
        with col2:
            st.metric("后100名平均收益", f"¥{bottom_100['最终收益值'].mean():,.0f}")
        with col3:
            advantage = ((top_100['最终收益值'].mean() - bottom_100['最终收益值'].mean()) / bottom_100[
                '最终收益值'].mean() * 100)
            st.metric("前100名优势", f"{advantage:.1f}%")

        # 创建对比条形图
        fig = px.bar(
            comparison_df,
            x='指标',
            y=['前100名平均值', '后100名平均值', '全量平均值'],
            title=f"{month} 前100名 vs 后100名 关键指标对比",
            barmode='group',
            labels={'value': '平均值', 'variable': '分组'},
            text_auto='.0f'
        )
        fig.update_layout(
            xaxis_title="指标",
            yaxis_title="平均值（元）",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # 显示优势百分比
        st.subheader("📈 前100名优势分析")

        # 创建优势百分比条形图
        fig2 = px.bar(
            comparison_df,
            x='指标',
            y='前100名优势百分比',
            title=f"{month} 前100名相对于后100名的优势百分比",
            color='前100名优势百分比',
            color_continuous_scale='RdYlGn',
            text_auto='.1f'
        )
        fig2.update_layout(
            xaxis_title="指标",
            yaxis_title="优势百分比 (%)",
            height=400
        )
        fig2.update_traces(texttemplate='%{y:.1f}%')
        st.plotly_chart(fig2, use_container_width=True)

        # 显示详细对比表格
        st.subheader("📋 详细对比数据")

        # 格式化显示
        display_df = comparison_df.copy()
        for col in ['前100名平均值', '后100名平均值', '全量平均值']:
            display_df[col] = display_df[col].apply(lambda x: f"¥{x:,.0f}" if pd.notnull(x) else "¥0")

        display_df['前100名优势百分比'] = display_df['前100名优势百分比'].apply(lambda x: f"{x:+.1f}%")
        display_df['前100名vs全量优势百分比'] = display_df['前100名vs全量优势百分比'].apply(lambda x: f"{x:+.1f}%")

        st.dataframe(display_df, use_container_width=True)

        # 显示关键发现
        st.subheader("💡 关键发现与建议")

        # 找出最大优势指标
        max_advantage_row = comparison_df.loc[comparison_df['前100名优势百分比'].idxmax()]
        max_advantage_metric = max_advantage_row['指标']
        max_advantage = max_advantage_row['前100名优势百分比']

        # 找出最小优势指标（可能是劣势）
        min_advantage_row = comparison_df.loc[comparison_df['前100名优势百分比'].idxmin()]
        min_advantage_metric = min_advantage_row['指标']
        min_advantage = min_advantage_row['前100名优势百分比']

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"**最大优势**: 前100名在 **{max_advantage_metric}** 上领先后100名 **{max_advantage:.1f}%**")
            st.info("✅ 建议: 继续保持这一优势，将此成功经验推广到其他顾问")

        with col2:
            if min_advantage < 0:
                st.error(f"**需关注**: 前100名在 **{min_advantage_metric}** 上仅领先后100名 **{min_advantage:.1f}%**")
                st.warning("⚠️ 建议: 需要加强此方面的培训和资源支持")
            else:
                st.info(f"**相对弱项**: 前100名在 **{min_advantage_metric}** 上领先优势较小 (**{min_advantage:.1f}%**)")
                st.info("💡 建议: 仍有提升空间，可针对性优化")

        # 顾问类型分布对比
        if '顾问编制' in df.columns:
            st.subheader("👥 顾问类型分布对比")

            top_types = top_100['顾问编制'].value_counts()
            bottom_types = bottom_100['顾问编制'].value_counts()

            col1, col2 = st.columns(2)

            with col1:
                st.write("**前100名顾问类型分布**")
                fig3 = px.pie(
                    values=top_types.values,
                    names=top_types.index,
                    title="前100名顾问类型分布"
                )
                st.plotly_chart(fig3, use_container_width=True)

            with col2:
                st.write("**后100名顾问类型分布**")
                fig4 = px.pie(
                    values=bottom_types.values,
                    names=bottom_types.index,
                    title="后100名顾问类型分布"
                )
                st.plotly_chart(fig4, use_container_width=True)

    def show_upload_instructions(self):
        """显示上传说明"""
        st.markdown("## 📋 使用说明")
        st.markdown("### 文件上传要求")
        st.markdown("1. **文件格式**: Excel文件 (.xlsx)")
        st.markdown("2. **命名规范**: 建议使用 `利润模型评估报告_原始收益值_YYYYMM.xlsx` 格式")
        st.markdown("3. **数据列要求**:")
        st.markdown("   - 时间/月份")
        st.markdown("   - 大区、区域、门店名称")
        st.markdown("   - 顾问名称、顾问编制")
        st.markdown("   - 最终收益值、销售利润")
        st.markdown("   - 新客贡献、会员价值贡献等关键指标")
        st.markdown("### 操作步骤")
        st.markdown("1. 通过左侧边栏上传一个或多个Excel文件")
        st.markdown("2. 选择要分析的月份")
        st.markdown("3. 查看各项分析报告和图表")
        st.markdown("### 支持的功能")
        st.markdown("- 📊 多维度绩效分析")
        st.markdown("- 📈 趋势对比")
        st.markdown("- 🔍 区域优劣势分析")
        st.markdown("- 🏆 绩效排名分析")
        st.markdown("- 📈 会员价值贡献分析")
        st.markdown("- 💾 数据导出功能")


def main():
    """主函数"""
    st.title("🏢 营养顾问绩效评估系统")
    st.markdown("---")

    dashboard = NutritionAdviserDashboard()

    st.sidebar.title("📁 数据上传")

    with st.sidebar.expander("📋 上传说明", expanded=True):
        st.markdown("- 支持多个Excel文件同时上传")
        st.markdown("- 文件命名建议: `利润模型评估报告_原始收益值_YYYYMM.xlsx`")
        st.markdown("- 系统自动从文件名识别月份")

    uploaded_files = st.sidebar.file_uploader(
        "上传Excel文件",
        type=["xlsx"],
        accept_multiple_files=True,
        help="请上传利润模型评估报告Excel文件"
    )

    if uploaded_files:
        dashboard.load_data_from_upload(uploaded_files)

    available_months = dashboard.get_available_months()
    if available_months:
        selected_month = st.sidebar.selectbox(
            "选择查看月份",
            options=available_months,
            index=0
        )

        # 创建概览仪表板
        dashboard.create_overview_dashboard(selected_month)

        st.markdown("---")
        st.header("📋 详细数据分析")

        # 创建选项卡
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "原始数据",
            "绩效排名",
            "前100vs后100分析",
            "区域详情",
            "数据导出",
            "会员价值贡献"
        ])

        with tab1:
            df = dashboard.get_month_data(selected_month)
            if not df.empty:
                st.subheader(f"{selected_month} - 原始数据")
                st.dataframe(df, use_container_width=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总记录数", len(df))
                with col2:
                    st.metric("数据列数", len(df.columns))
                with col3:
                    st.metric("数据大小", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
            else:
                st.warning("没有数据可显示")

        with tab2:
            df = dashboard.get_month_data(selected_month)
            if not df.empty and '最终收益值' in df.columns:
                st.subheader("🏆 绩效排名分析")

                col1, col2, col3 = st.columns(3)
                with col1:
                    rank_by = st.selectbox(
                        "排名依据",
                        options=["最终收益值", "销售利润", "总收益"] if '总收益' in df.columns else ["最终收益值",
                                                                                                     "销售利润"],
                        index=0
                    )
                with col2:
                    rank_type = st.selectbox("排名类型", options=["前N名", "后N名"], index=0)
                with col3:
                    top_n = st.slider("显示人数", 10, min(100, len(df)), 20)

                if rank_type == "前N名":
                    ranked_df = df.nlargest(top_n, rank_by)
                    rank_title = f"前{top_n}名"
                else:
                    ranked_df = df.nsmallest(top_n, rank_by)
                    rank_title = f"后{top_n}名"

                st.subheader(f"{rank_title}绩效排名")

                display_columns = []
                for col in ['顾问名称', '顾问编制', '大区', '区域', '门店名称',
                            '最终收益值', '销售利润', '总收益']:
                    if col in ranked_df.columns:
                        display_columns.append(col)

                ranked_df = ranked_df[display_columns]
                ranked_df['排名'] = range(1, len(ranked_df) + 1)
                cols = ['排名'] + [col for col in ranked_df.columns if col != '排名']
                ranked_df = ranked_df[cols]

                st.markdown('<div class="scrollable-table">', unsafe_allow_html=True)
                st.dataframe(ranked_df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                csv = ranked_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"下载{rank_title}排名数据(CSV)",
                    data=csv,
                    file_name=f"{rank_title}_{selected_month}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("没有排名数据可显示")

        with tab3:
            df = dashboard.get_month_data(selected_month)
            if not df.empty and '最终收益值' in df.columns:
                # 创建前100名与后100名对比分析
                dashboard.create_performance_comparison(df, selected_month)
            else:
                st.warning("没有足够的数据进行对比分析")

        with tab4:
            df = dashboard.get_month_data(selected_month)
            if not df.empty and '大区' in df.columns:
                regions = df['大区'].unique()
                selected_region = st.selectbox("选择大区", options=regions)
                region_data = df[df['大区'] == selected_region]

                if not region_data.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(f"{selected_region} - 关键指标")
                        st.metric("顾问人数", len(region_data))
                        if '最终收益值' in region_data.columns:
                            st.metric("平均收益", f"¥{region_data['最终收益值'].mean():,.0f}")
                            st.metric("总收益", f"¥{region_data['最终收益值'].sum():,.0f}")
                    with col2:
                        st.subheader("顾问类型分布")
                        if '顾问编制' in region_data.columns:
                            type_dist = region_data['顾问编制'].value_counts()
                            fig = px.pie(
                                values=type_dist.values,
                                names=type_dist.index,
                                title=f"{selected_region} 顾问类型分布"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                    st.subheader("详细数据")
                    st.dataframe(region_data, use_container_width=True)
                else:
                    st.warning(f"没有找到 {selected_region} 的数据")
            else:
                st.warning("没有区域数据可显示")

        with tab5:
            df = dashboard.get_month_data(selected_month)
            if not df.empty:
                st.subheader("数据导出功能")
                col1, col2 = st.columns(2)

                with col1:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="下载完整数据(CSV)",
                        data=csv,
                        file_name=f"营养顾问数据_{selected_month}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                with col2:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='原始数据')
                        if '大区' in df.columns and '最终收益值' in df.columns:
                            summary = df.groupby('大区').agg({
                                '最终收益值': ['count', 'mean', 'sum']
                            }).round(0)
                            summary.columns = ['人数', '平均收益', '总收益']
                            summary.to_excel(writer, sheet_name='区域汇总')

                    excel_data = output.getvalue()
                    st.download_button(
                        label="下载完整数据(Excel)",
                        data=excel_data,
                        file_name=f"营养顾问数据_{selected_month}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                st.info("💡 导出的数据包含完整的原始记录和统计信息")
            else:
                st.warning("没有数据可导出")

        with tab6:
            # 创建会员价值贡献分析
            dashboard.create_member_value_analysis(selected_month)

    else:
        dashboard.show_upload_instructions()

        with st.expander("📊 示例数据结构参考", expanded=False):
            sample_data = {
                '月份': ['2024年01月', '2024年01月'],
                '大区': ['华北区', '华东区'],
                '区域': ['北京', '上海'],
                '门店名称': ['门店A', '门店B'],
                '顾问名称': ['张三', '李四'],
                '顾问编制': ['全职', '兼职'],
                '最终收益值': [50000, 75000],
                '销售利润': [45000, 68000],
                '新客贡献': [5000, 7000],
                '会员价值贡献': [3000, 4500],
                '试饮获客贡献': [2000, 3000],
                'A+B内码贡献': [1000, 1500],
                '总收益': [56000, 84000]
            }
            sample_df = pd.DataFrame(sample_data)
            st.dataframe(sample_df, use_container_width=True)


if __name__ == "__main__":
    main()
