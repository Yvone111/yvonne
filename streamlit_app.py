import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
import warnings
import requests
import io
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

# 自定义CSS样式
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1 {
        font-size: 1.8rem !important;
    }
    h2 {
        font-size: 1.5rem !important;
    }
    h3 {
        font-size: 1.3rem !important;
    }
    .stMetric {
        font-size: 0.9rem !important;
    }
    .css-1d391kg {
        font-size: 0.9rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
    .github-info {
        background-color: #f0f8ff;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #0366d6;
        margin: 10px 0;
    }
    .data-source-selector {
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


class NutritionAdviserDashboard:
    def __init__(self):
        """营养顾问绩效评估仪表板"""
        self.monthly_data = {}
        self.data_source = "github"  # 默认使用GitHub源

    def load_from_github(self):
        """从GitHub仓库加载Excel文件"""
        try:
            # 获取当前文件的目录
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # 查找当前目录下的Excel文件
            pattern = os.path.join(current_dir, "利润模型评估报告_原始收益值_*.xlsx")
            excel_files = glob.glob(pattern)

            if not excel_files:
                st.sidebar.warning("在GitHub仓库中没有找到Excel文件")
                st.sidebar.info("请确保Excel文件与app.py在同一目录下")
                return False

            st.sidebar.success(f"✅ 从GitHub仓库找到 {len(excel_files)} 个Excel文件")

            for file_path in excel_files:
                try:
                    # 从文件名提取月份信息
                    filename = os.path.basename(file_path)

                    if "利润模型评估报告_原始收益值_" in filename:
                        date_str = filename.replace("利润模型评估报告_原始收益值_", "").replace(".xlsx", "")

                        # 尝试解析日期
                        try:
                            file_date = datetime.strptime(date_str, "%Y%m")
                            month_key = file_date.strftime("%Y年%m月")

                            # 读取Excel文件
                            df = pd.read_excel(file_path)

                            # 添加月份标识列
                            df['月份'] = month_key
                            df['日期'] = file_date
                            df['数据来源'] = 'GitHub仓库'

                            # 存储数据
                            self.monthly_data[month_key] = {
                                'data': df,
                                'date': file_date,
                                'file_path': filename,
                                'source': 'github'
                            }

                            st.sidebar.success(f"✅ 已加载: {month_key}")

                        except ValueError as e:
                            st.sidebar.warning(f"文件名日期格式不正确 {filename}: {str(e)}")

                except Exception as e:
                    st.sidebar.error(f"加载文件失败 {file_path}: {str(e)}")

            return len(excel_files) > 0

        except Exception as e:
            st.sidebar.error(f"从GitHub加载数据失败: {str(e)}")
            return False

    def load_from_upload(self, uploaded_files):
        """从上传的文件加载数据"""
        if not uploaded_files:
            return False

        loaded_count = 0
        for uploaded_file in uploaded_files:
            try:
                # 从文件名提取月份信息
                filename = uploaded_file.name

                # 提取月份
                if "利润模型评估报告_原始收益值_" in filename:
                    date_str = filename.replace("利润模型评估报告_原始收益值_", "").replace(".xlsx", "")
                    try:
                        file_date = datetime.strptime(date_str, "%Y%m")
                        month_key = file_date.strftime("%Y年%m月")
                    except:
                        month_key = filename.replace(".xlsx", "")
                else:
                    month_key = filename.replace(".xlsx", "")

                # 读取Excel文件
                df = pd.read_excel(uploaded_file)

                # 添加月份标识列
                df['月份'] = month_key
                df['日期'] = datetime.now()
                df['数据来源'] = '上传文件'

                # 存储数据
                self.monthly_data[month_key] = {
                    'data': df,
                    'date': datetime.now(),
                    'file_path': f"上传文件: {filename}",
                    'source': 'uploaded'
                }

                loaded_count += 1
                st.sidebar.success(f"✅ 已加载上传文件: {month_key} (共{len(df)}条记录)")

            except Exception as e:
                st.sidebar.error(f"❌ 处理上传文件 {uploaded_file.name} 时出错: {str(e)}")

        return loaded_count > 0

    def set_data_source(self, source):
        """设置数据源"""
        self.data_source = source

    def clear_data(self):
        """清空数据"""
        self.monthly_data = {}

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
            return months[current_index + 1]  # 因为是倒序排列
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

    def create_overview_dashboard(self, selected_month):
        """创建概览仪表板"""
        st.header(f"📊 营养顾问绩效评估概览 - {selected_month}")

        df = self.get_month_data(selected_month)
        if df.empty:
            st.warning(f"没有找到 {selected_month} 的数据")
            return

        # 显示数据来源
        if selected_month in self.monthly_data:
            data_source_info = self.monthly_data[selected_month]
            source_type = data_source_info.get('source', 'unknown')
            if source_type == 'github':
                data_source = "GitHub仓库"
            elif source_type == 'uploaded':
                data_source = "上传文件"
            else:
                data_source = "未知"
            st.caption(f"📁 数据来源: {data_source}")

        # 关键指标卡片
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
            # 计算高绩效顾问比例（收益前20%）
            if '最终收益值' in df.columns and len(df) > 0:
                threshold = df['最终收益值'].quantile(0.8)
                high_performers = len(df[df['最终收益值'] >= threshold])
                percentage = (high_performers / len(df)) * 100
                st.metric("高绩效顾问比例", f"{percentage:.1f}%")
            else:
                st.metric("高绩效顾问比例", "0%")

        # 第一行：收益分布和顾问类型分析
        col1, col2 = st.columns(2)

        with col1:
            self.create_profit_distribution_chart(df, selected_month)

        with col2:
            self.create_adviser_type_chart(df, selected_month)

        # 第二行：大区分析和时间趋势
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

        # 收益分段
        profit_bins = [-float('inf'), 0, 10000, 50000, 100000, 200000, float('inf')]
        profit_labels = ['亏损(<0)', '低收益(0-1万)', '中低收益(1-5万)',
                         '中收益(5-10万)', '中高收益(10-20万)', '高收益(>20万)']

        df_copy = df.copy()
        df_copy['收益分段'] = pd.cut(df_copy['最终收益值'], bins=profit_bins, labels=profit_labels)
        distribution = df_copy['收益分段'].value_counts().reindex(profit_labels)

        # 创建饼图
        fig = px.pie(
            values=distribution.values,
            names=distribution.index,
            title=f"{month} 收益分布",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=False, height=400)

        st.plotly_chart(fig, use_container_width=True)

        # 显示统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("最高收益", f"¥{df['最终收益值'].max():,.0f}")
        with col2:
            st.metric("中位数", f"¥{df['最终收益值'].median():,.0f}")
        with col3:
            st.metric("最低收益", f"¥{df['最终收益值'].min():,.0f}")

    def create_adviser_type_chart(self, df, month):
        """创建顾问类型分析图表 - 简化版本，只显示平均收益图表"""
        st.subheader("👥 各类型顾问表现")

        if '顾问编制' not in df.columns or '最终收益值' not in df.columns:
            st.warning("缺少必要的数据列")
            return

        # 按顾问类型分组统计
        type_stats = df.groupby('顾问编制').agg({
            '最终收益值': ['count', 'mean', 'median', 'std']
        }).round(0)

        # 简化列名
        type_stats.columns = ['人数', '平均收益', '中位收益', '标准差']
        type_stats = type_stats.reset_index()

        # 创建柱状图
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

        # 显示简单统计表
        st.subheader("各类型顾问基本统计")
        display_stats = type_stats[['顾问编制', '人数', '平均收益']]
        display_stats.columns = ['顾问类型', '人数', '平均收益(元)']
        display_stats['平均收益(元)'] = display_stats['平均收益(元)'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(display_stats, use_container_width=True)

    def create_region_analysis_chart(self, df, month):
        """创建大区分析图表 - 简化版本"""
        st.subheader("🌍 大区绩效分析")

        if '大区' not in df.columns or '最终收益值' not in df.columns:
            st.warning("缺少大区数据")
            return

        # 按大区分组统计
        region_stats = df.groupby('大区').agg({
            '最终收益值': ['mean', 'count']
        }).round(0)

        region_stats.columns = ['平均收益', '顾问人数']
        region_stats = region_stats.reset_index()

        if len(region_stats) == 0:
            st.warning("没有大区数据可显示")
            return

        # 按平均收益排序
        region_stats = region_stats.sort_values('平均收益', ascending=True)

        # 创建水平条形图 - 更简洁
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

        # 识别强项和弱项区域
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

        # 显示详细数据表
        st.subheader("各区域详细数据")
        display_data = region_stats[['大区', '顾问人数', '平均收益']]
        display_data.columns = ['大区', '顾问人数', '平均收益(元)']
        display_data = display_data.sort_values('平均收益(元)', ascending=False)
        st.dataframe(display_data, use_container_width=True)

    def create_trend_analysis_chart(self, selected_month):
        """创建趋势分析图表"""
        st.subheader("📅 多月份趋势分析")

        if len(self.monthly_data) < 2:
            st.info("需要至少两个月份的数据才能进行趋势分析")
            return

        # 准备趋势数据
        trend_data = []
        for month, data_info in self.monthly_data.items():
            df = data_info['data']
            if '最终收益值' in df.columns and '顾问编制' in df.columns:
                # 总体平均收益
                overall_avg = df['最终收益值'].mean()

                # 各类型顾问平均收益
                type_avgs = df.groupby('顾问编制')['最终收益值'].mean().to_dict()

                trend_data.append({
                    '月份': month,
                    '日期': data_info['date'],
                    '总体平均收益': overall_avg,
                    **type_avgs
                })

        if not trend_data:
            st.warning("没有足够的数据进行趋势分析")
            return

        trend_df = pd.DataFrame(trend_data)
        trend_df = trend_df.sort_values('日期')

        # 创建趋势图
        fig = go.Figure()

        # 添加总体平均线
        fig.add_trace(go.Scatter(
            x=trend_df['月份'],
            y=trend_df['总体平均收益'],
            mode='lines+markers',
            name='总体平均',
            line=dict(width=4)
        ))

        # 添加各类型顾问趋势线
        adviser_types = [col for col in trend_df.columns if col not in ['月份', '日期', '总体平均收益']]
        colors = px.colors.qualitative.Set2

        for i, adviser_type in enumerate(adviser_types):
            if adviser_type in trend_df.columns:
                fig.add_trace(go.Scatter(
                    x=trend_df['月份'],
                    y=trend_df[adviser_type],
                    mode='lines+markers',
                    name=adviser_type,
                    line=dict(width=2, dash='dot'),
                    marker=dict(size=6),
                    line_shape='spline'
                ))

        fig.update_layout(
            title="各类型顾问收益趋势",
            xaxis_title="月份",
            yaxis_title="平均收益（元）",
            height=400,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # 显示变化情况
        st.subheader("月度变化分析")
        if len(trend_df) > 1:
            latest = trend_df.iloc[-1]
            previous = trend_df.iloc[-2]

            change = latest['总体平均收益'] - previous['总体平均收益']
            change_percent = (change / previous['总体平均收益']) * 100

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "总体平均收益",
                    f"¥{latest['总体平均收益']:,.0f}",
                    f"{change_percent:+.1f}%"
                )

            with col2:
                # 计算表现最好的顾问类型
                best_type = None
                best_value = -float('inf')
                for col in adviser_types:
                    if col in latest and col in previous:
                        change_val = latest[col] - previous[col]
                        if change_val > best_value:
                            best_value = change_val
                            best_type = col

                if best_type:
                    st.metric(
                        "进步最大类型",
                        best_type,
                        f"¥{best_value:+.0f}"
                    )

    def create_sales_profit_analysis(self, selected_month):
        """创建销售利润分布分析 - 新增选项卡"""
        st.header(f"📊 销售利润分布分析 - {selected_month}")

        df = self.get_month_data(selected_month)
        if df.empty:
            st.warning(f"没有找到 {selected_month} 的数据")
            return

        # 检查是否有销售利润列
        if '销售利润' not in df.columns or '顾问编制' not in df.columns:
            st.warning("缺少销售利润或顾问编制数据")
            return

        # 定义销售利润坎级
        sales_bins = [0, 20000, 50000, 100000, float('inf')]
        sales_labels = ['2万以下', '2-5万', '5-10万', '10万以上']

        # 为每个顾问添加销售利润坎级
        df_copy = df.copy()
        df_copy['销售利润坎级'] = pd.cut(df_copy['销售利润'], bins=sales_bins, labels=sales_labels)

        # 计算各类型顾问在不同坎级的人数
        sales_distribution = df_copy.groupby(['顾问编制', '销售利润坎级']).size().unstack(fill_value=0)

        # 计算各坎级占比
        sales_percentage = sales_distribution.div(sales_distribution.sum(axis=1), axis=0) * 100

        # 合并数量和占比
        sales_summary = pd.DataFrame()
        for label in sales_labels:
            if label in sales_distribution.columns:
                sales_summary[f'{label}人数'] = sales_distribution[label]

        # 添加总人数
        sales_summary['总人数'] = sales_distribution.sum(axis=1)
        sales_summary = sales_summary.reset_index()

        # 重命名列
        sales_summary.columns.name = ''

        # 显示表格
        st.subheader("各类型顾问销售利润分布统计")
        st.dataframe(sales_summary, use_container_width=True)

        # 销售利润分布可视化 - 两个图表横向并排
        st.subheader("销售利润分布可视化")
        col1, col2 = st.columns(2)

        with col1:
            # 利润分布图表
            st.subheader("利润分布")
            self.create_stacked_bar_chart(sales_distribution, selected_month, "left")

        with col2:
            # 利润分布百分比图表
            st.subheader("利润分布百分比")
            self.create_stacked_percentage_chart(sales_percentage, selected_month, "right")

    def create_stacked_bar_chart(self, sales_distribution, month, key_suffix=""):
        """使用go.Figure创建堆叠条形图"""
        # 获取顾问类型和坎级标签
        adviser_types = sales_distribution.index.tolist()
        sales_labels = sales_distribution.columns.tolist()

        # 创建图形
        fig = go.Figure()

        # 定义颜色
        colors = ['#8dd3c7', '#ffffb4', '#bebadb', '#fb8072']

        # 为每个坎级添加一个条形图轨迹
        for i, label in enumerate(sales_labels):
            # 获取当前坎级的数据
            y_data = sales_distribution[label]

            # 创建文本标注
            text_positions = []
            for j, value in enumerate(y_data):
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
                hovertemplate=f"<b>{label}</b><br>顾问类型: %{{x}}<br>人数: %{{y}}<br><extra></extra>"
            ))

        # 更新布局
        fig.update_layout(
            title=dict(text=f"{month} 各类型顾问销售利润分布", font=dict(size=16)),
            xaxis=dict(title="顾问类型", title_font=dict(size=12), tickfont=dict(size=10)),
            yaxis=dict(title="人数", title_font=dict(size=12), tickfont=dict(size=10)),
            barmode='stack',
            height=400,
            showlegend=True,
            margin=dict(l=50, r=50, t=60, b=50),
        )

        # 确保y轴有足够的空间显示外部文本
        max_value = sales_distribution.sum(axis=1).max()
        fig.update_yaxes(range=[0, max_value * 1.15])

        # 使用唯一的key
        st.plotly_chart(fig, use_container_width=True, key=f"stacked_bar_{month}_{key_suffix}")

    def create_stacked_percentage_chart(self, sales_percentage, month, key_suffix=""):
        """使用go.Figure创建百分比堆叠条形图"""
        # 获取顾问类型和坎级标签
        adviser_types = sales_percentage.index.tolist()
        sales_labels = sales_percentage.columns.tolist()

        # 创建图形
        fig = go.Figure()

        # 定义颜色
        colors = ['#8dd3c7', '#ffffb4', '#bebadb', '#fb8072']

        # 为每个坎级添加一个条形图轨迹
        for i, label in enumerate(sales_labels):
            # 计算文本位置
            text_positions = []
            for j, value in enumerate(sales_percentage[label]):
                if value < 5:
                    text_positions.append('outside')
                else:
                    text_positions.append('inside')

            fig.add_trace(go.Bar(
                name=label,
                x=adviser_types,
                y=sales_percentage[label],
                text=[f"{v:.1f}%" for v in sales_percentage[label]],
                textposition=text_positions,
                textfont=dict(size=12, color='black'),
                marker_color=colors[i % len(colors)],
                hovertemplate=f"<b>{label}</b><br>顾问类型: %{{x}}<br>百分比: %{{y:.1f}}%<br><extra></extra>"
            ))

        # 更新布局
        fig.update_layout(
            title=f"{month} 各类型顾问销售利润分布百分比",
            xaxis_title="顾问类型",
            yaxis_title="百分比 (%)",
            barmode='stack',
            height=400,
            showlegend=True,
        )

        # 使用唯一的key
        st.plotly_chart(fig, use_container_width=True, key=f"stacked_percentage_{month}_{key_suffix}")

    def create_region_strengths_weaknesses(self, df, region, previous_month_data=None):
        """创建区域优势与劣势报告"""
        st.subheader(f"📋 {region} 区域优势与劣势分析")

        if df.empty or '大区' not in df.columns:
            st.warning("无法进行区域分析")
            return

        # 筛选指定区域数据
        region_data = df[df['大区'] == region]
        if region_data.empty:
            st.warning(f"没有找到 {region} 的数据")
            return

        # 计算区域平均值
        region_avg_sales = region_data['销售利润'].mean() if '销售利润' in region_data.columns else 0
        region_avg_new_customer = region_data['新客贡献'].mean() if '新客贡献' in region_data.columns else 0
        region_avg_member_value = region_data['会员价值贡献'].mean() if '会员价值贡献' in region_data.columns else 0
        region_avg_trial = region_data['试饮获客贡献'].mean() if '试饮获客贡献' in region_data.columns else 0
        region_avg_internal = region_data['A+B内码贡献'].mean() if 'A+B内码贡献' in region_data.columns else 0

        # 计算全区域平均值
        overall_avg_sales = df['销售利润'].mean() if '销售利润' in df.columns else 0
        overall_avg_new_customer = df['新客贡献'].mean() if '新客贡献' in df.columns else 0
        overall_avg_member_value = df['会员价值贡献'].mean() if '会员价值贡献' in df.columns else 0
        overall_avg_trial = df['试饮获客贡献'].mean() if '试饮获客贡献' in df.columns else 0
        overall_avg_internal = df['A+B内码贡献'].mean() if 'A+B内码贡献' in df.columns else 0

        # 优势与劣势分析
        st.subheader("✅ 优势与薄弱环节分析")

        # 创建指标数据框
        metrics_data = {
            '指标': ['销售利润', '新客贡献', '会员价值', '试饮获客', 'A+B内码贡献'],
            f'{region}区域平均值': [
                region_avg_sales,
                region_avg_new_customer,
                region_avg_member_value,
                region_avg_trial,
                region_avg_internal
            ],
            '全区域平均值': [
                overall_avg_sales,
                overall_avg_new_customer,
                overall_avg_member_value,
                overall_avg_trial,
                overall_avg_internal
            ]
        }

        metrics_df = pd.DataFrame(metrics_data)
        metrics_df['差异'] = metrics_df[f'{region}区域平均值'] - metrics_df['全区域平均值']
        metrics_df['差异百分比'] = (metrics_df['差异'] / metrics_df['全区域平均值'] * 100).round(1)
        metrics_df = metrics_df.fillna(0)

        # 使用百分比差异条形图
        st.subheader("📊 与全区域平均的百分比差异")

        # 创建百分比差异条形图
        fig = px.bar(
            metrics_df,
            x='差异百分比',
            y='指标',
            orientation='h',
            title=f"{region}区域 vs 全区域平均 - 百分比差异",
            color='差异百分比',
            color_continuous_scale='RdYlGn',
            text_auto='.1f'
        )
        fig.update_layout(
            xaxis_title="与全区域平均的差异百分比 (%)",
            yaxis_title="指标",
            height=400
        )
        fig.update_traces(texttemplate='%{x:.1f}%', textposition='outside')

        st.plotly_chart(fig, use_container_width=True)

        # 使用并列条形图显示实际数值
        st.subheader("📈 各指标实际数值对比")

        # 准备数据用于并列条形图
        comparison_data = []
        for _, row in metrics_df.iterrows():
            comparison_data.append({
                '指标': row['指标'],
                '数值': row[f'{region}区域平均值'],
                '类型': f'{region}区域'
            })
            comparison_data.append({
                '指标': row['指标'],
                '数值': row['全区域平均值'],
                '类型': '全区域平均'
            })

        comparison_df = pd.DataFrame(comparison_data)

        # 创建并列条形图
        fig2 = px.bar(
            comparison_df,
            x='指标',
            y='数值',
            color='类型',
            barmode='group',
            title=f"{region}区域 vs 全区域平均 - 实际数值对比",
            text_auto='.0f'
        )
        fig2.update_layout(
            xaxis_title="指标",
            yaxis_title="数值（元）",
            height=400
        )

        st.plotly_chart(fig2, use_container_width=True)

        # 使用表格显示详细数据
        st.subheader("📋 详细指标数据")

        # 格式化数值显示
        display_df = metrics_df.copy()
        for col in [f'{region}区域平均值', '全区域平均值', '差异']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"¥{x:,.0f}" if pd.notnull(x) else "¥0")

        display_df['差异百分比'] = display_df['差异百分比'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "0.0%")

        # 添加颜色标记函数
        def color_percentage(val):
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

        # 显示表格
        styled_df = display_df.style.applymap(color_percentage, subset=['差异百分比'])
        st.dataframe(styled_df, use_container_width=True)

        # 显示关键绩效指标
        st.subheader("🎯 关键绩效指标")

        # 选择最重要的3个指标进行KPI展示
        top_metrics = metrics_df.nlargest(3, '差异百分比')
        bottom_metrics = metrics_df.nsmallest(3, '差异百分比')

        col1, col2, col3 = st.columns(3)
        metrics_cols = [col1, col2, col3]

        for i, (_, row) in enumerate(top_metrics.iterrows()):
            with metrics_cols[i]:
                metric_value = row['差异百分比']
                metric_name = row['指标']

                if metric_value > 0:
                    st.metric(
                        label=f"✅ {metric_name}",
                        value=f"+{metric_value:.1f}%",
                        delta=f"优于平均 {metric_value:.1f}%"
                    )
                else:
                    st.metric(
                        label=f"⚠️ {metric_name}",
                        value=f"{metric_value:.1f}%",
                        delta=f"低于平均 {abs(metric_value):.1f}%"
                    )

        # 显示总结分析
        st.subheader("📝 区域表现总结")

        # 计算优势指标数量
        advantage_count = len(metrics_df[metrics_df['差异百分比'] > 0])
        disadvantage_count = len(metrics_df[metrics_df['差异百分比'] < 0])

        col1, col2 = st.columns(2)

        with col1:
            if advantage_count > 0:
                st.success(f"**优势领域**: {region}区域在 {advantage_count} 个指标上优于全区域平均")
                # 列出具体优势指标
                advantage_metrics = metrics_df[metrics_df['差异百分比'] > 0]['指标'].tolist()
                st.write(f"优势指标: {', '.join(advantage_metrics)}")
            else:
                st.info("**暂无显著优势指标**")

        with col2:
            if disadvantage_count > 0:
                st.error(f"**需改进领域**: {region}区域在 {disadvantage_count} 个指标上低于全区域平均")
                # 列出具体需改进指标
                disadvantage_metrics = metrics_df[metrics_df['差异百分比'] < 0]['指标'].tolist()
                st.write(f"需改进指标: {', '.join(disadvantage_metrics)}")
            else:
                st.success("**所有指标均达到或超过全区域平均水平**")

        # 提供改进建议
        if disadvantage_count > 0:
            st.subheader("💡 改进建议")

            # 找出差异最大的需改进指标
            if not metrics_df[metrics_df['差异百分比'] < 0].empty:
                worst_metric = metrics_df[metrics_df['差异百分比'] < 0].nsmallest(1, '差异百分比').iloc[0]
                worst_metric_name = worst_metric['指标']
                worst_metric_gap = abs(worst_metric['差异百分比'])

                st.info(
                    f"**重点关注**: {worst_metric_name} 指标低于全区域平均 {worst_metric_gap:.1f}%，建议优先改进此领域。")

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

def main():
        """主函数"""
        st.title("🏢 营养顾问绩效评估系统")
        st.markdown("---")

        # 初始化session state
        if 'dashboard' not in st.session_state:
            st.session_state.dashboard = NutritionAdviserDashboard()
            st.session_state.data_loaded = False
            st.session_state.current_data_source = "github"

        # 侧边栏 - 数据源选择
        st.sidebar.title("📁 数据源配置")

        # 数据源选择
        data_source = st.sidebar.radio(
            "选择数据源",
            ["GitHub仓库", "文件上传"],
            index=0,
            help="选择从GitHub仓库自动读取Excel文件，或手动上传Excel文件"
        )

        # 根据选择的数据源显示相应界面
        if data_source == "GitHub仓库":
            st.sidebar.markdown("---")
            st.sidebar.subheader("🔗 GitHub仓库数据")

            # 显示GitHub仓库信息
            current_dir = os.path.dirname(os.path.abspath(__file__))
            st.sidebar.info(f"当前目录: {current_dir}")

            # 检查当前目录下有哪些Excel文件
            excel_files = glob.glob(os.path.join(current_dir, "利润模型评估报告_原始收益值_*.xlsx"))

            if excel_files:
                st.sidebar.success(f"✅ 在仓库中找到 {len(excel_files)} 个Excel文件")
                with st.sidebar.expander("📂 查看文件列表"):
                    for file in excel_files:
                        filename = os.path.basename(file)
                        st.sidebar.text(f"• {filename}")
            else:
                st.sidebar.warning("⚠️ 在仓库中未找到Excel文件")
                st.sidebar.info("请确保Excel文件与app.py在同一目录下")

            # 加载GitHub数据按钮
            if st.sidebar.button("🔄 加载GitHub数据", type="primary"):
                with st.spinner("正在从GitHub仓库加载数据..."):
                    success = st.session_state.dashboard.load_from_github()
                    if success:
                        st.session_state.data_loaded = True
                        st.session_state.current_data_source = "github"
                        st.sidebar.success("✅ 数据加载完成！")
                        st.rerun()
                    else:
                        st.sidebar.error("❌ 数据加载失败")

        elif data_source == "文件上传":
            st.sidebar.markdown("---")
            st.sidebar.subheader("📤 文件上传")

            uploaded_files = st.sidebar.file_uploader(
                "选择Excel文件",
                type=["xlsx"],
                accept_multiple_files=True,
                help="请上传利润模型评估报告Excel文件。支持多文件上传。"
            )

            if uploaded_files:
                if st.sidebar.button("📥 加载上传数据", type="primary"):
                    with st.spinner("正在处理上传的文件..."):
                        # 清空现有数据
                        st.session_state.dashboard.clear_data()

                        # 加载上传文件
                        success = st.session_state.dashboard.load_from_upload(uploaded_files)
                        if success:
                            st.session_state.data_loaded = True
                            st.session_state.current_data_source = "upload"
                            st.sidebar.success("✅ 上传数据加载完成！")
                            st.rerun()
                        else:
                            st.sidebar.error("❌ 数据加载失败")

        # 显示当前数据状态
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 数据状态")

        available_months = st.session_state.dashboard.get_available_months()
        if available_months:
            st.sidebar.success(f"✅ 已加载 {len(available_months)} 个月份的数据")
            st.sidebar.info(
                f"📅 可用月份: {', '.join(available_months[:3])}{'...' if len(available_months) > 3 else ''}")
        else:
            st.sidebar.warning("⚠️ 暂无数据")
            st.sidebar.info("请先选择数据源并加载数据")

        # 清除数据按钮
        if st.sidebar.button("🗑️ 清除所有数据"):
            st.session_state.dashboard.clear_data()
            st.session_state.data_loaded = False
            st.sidebar.success("✅ 数据已清除")
            st.rerun()

        # 主界面
        available_months = st.session_state.dashboard.get_available_months()
        if available_months:
            selected_month = st.sidebar.selectbox(
                "选择查看月份",
                options=available_months,
                index=0
            )

            # 获取上月数据
            previous_month = st.session_state.dashboard.get_previous_month(selected_month)
            previous_month_data = None
            if previous_month:
                previous_month_data = st.session_state.dashboard.get_month_data(previous_month)

            # 显示数据概览
            st.session_state.dashboard.create_overview_dashboard(selected_month)

            # 添加详细数据选项卡
            st.markdown("---")
            st.header("📋 详细数据查看")

            # 增加销售利润分析选项卡
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "原始数据", "绩效排名", "前100vs后100分析", "区域详情",
                "区域分析报告", "会员价值贡献", "销售利润分析"
            ])

            with tab1:
                df = st.session_state.dashboard.get_month_data(selected_month)
                if not df.empty:
                    st.dataframe(df, use_container_width=True)

                    # 添加数据下载功能
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="下载CSV格式数据",
                        data=csv,
                        file_name=f"营养顾问数据_{selected_month}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("没有数据可显示")

            with tab2:
                df = st.session_state.dashboard.get_month_data(selected_month)
                if not df.empty and '最终收益值' in df.columns:
                    # 添加排名选项 - 使用3列布局
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        rank_by = st.selectbox(
                            "排名依据",
                            options=["最终收益值", "销售利润", "总收益"],
                            index=0
                        )
                    with col2:
                        rank_type = st.selectbox(
                            "排名类型",
                            options=["前N名", "后N名"],
                            index=0
                        )
                    with col3:
                        top_n = st.slider("显示N名", 10, min(200, len(df)), 20)

                    # 计算排名
                    if rank_type == "前N名":
                        ranked_df = df.nlargest(top_n, rank_by)
                        rank_title = f"前{top_n}名"
                    else:
                        ranked_df = df.nsmallest(top_n, rank_by)
                        rank_title = f"后{top_n}名"

                    st.subheader(f"{rank_title}绩效排名")

                    # 选择要显示的列
                    display_columns = []
                    for col in ['顾问名称', '顾问编制', '大区', '区域', '门店名称',
                                '最终收益值', '销售利润', '总收益']:
                        if col in ranked_df.columns:
                            display_columns.append(col)

                    ranked_df = ranked_df[display_columns]
                    ranked_df['排名'] = range(1, len(ranked_df) + 1)

                    # 重新排列列顺序，将排名放在第一列
                    cols = ['排名'] + [col for col in ranked_df.columns if col != '排名']
                    ranked_df = ranked_df[cols]

                    st.dataframe(ranked_df, use_container_width=True)
                else:
                    st.warning("没有排名数据可显示")

            with tab3:
                df = st.session_state.dashboard.get_month_data(selected_month)
                if not df.empty and '最终收益值' in df.columns:
                    # 创建前100名与后100名对比分析
                    st.session_state.dashboard.create_performance_comparison(df, selected_month)
                else:
                    st.warning("没有足够的数据进行对比分析")

            with tab4:
                df = st.session_state.dashboard.get_month_data(selected_month)
                if not df.empty and '大区' in df.columns:
                    # 选择要查看的大区
                    regions = df['大区'].unique()
                    selected_region = st.selectbox("选择大区", options=regions)

                    region_data = df[df['大区'] == selected_region]

                    if not region_data.empty:
                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader(f"{selected_region} - 关键指标")
                            st.metric("顾问人数", len(region_data))
                            st.metric("平均收益", f"¥{region_data['最终收益值'].mean():,.0f}")
                            st.metric("总收益", f"¥{region_data['最终收益值'].sum():,.0f}")

                        with col2:
                            st.subheader("顾问类型分布")
                            type_dist = region_data['顾问编制'].value_counts()
                            fig = px.pie(
                                values=type_dist.values,
                                names=type_dist.index,
                                title=f"{selected_region} 顾问类型分布"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        # 显示该区域详细数据
                        st.subheader("详细数据")
                        st.dataframe(region_data, use_container_width=True)
                    else:
                        st.warning(f"没有找到 {selected_region} 的数据")
                else:
                    st.warning("没有区域数据可显示")

            with tab5:
                df = st.session_state.dashboard.get_month_data(selected_month)
                if not df.empty and '大区' in df.columns:
                    # 选择要分析的大区
                    regions = df['大区'].unique()
                    selected_region = st.selectbox("选择要分析的大区", options=regions, key="analysis_region")

                    # 创建区域优势与劣势报告
                    st.session_state.dashboard.create_region_strengths_weaknesses(df, selected_region,
                                                                                  previous_month_data)
                else:
                    st.warning("没有区域数据可显示")

            with tab6:
                # 创建会员价值贡献分析
                st.session_state.dashboard.create_member_value_analysis(selected_month)

            with tab7:
                # 新增销售利润分析选项卡
                st.session_state.dashboard.create_sales_profit_analysis(selected_month)

        else:
            # 显示欢迎界面和使用说明
            st.info("👈 请先选择数据源并加载数据")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                    ## 📁 数据源说明

                    ### 1. GitHub仓库模式
                    - 自动读取与`app.py`在同一目录下的Excel文件
                    - 文件命名格式: `利润模型评估报告_原始收益值_YYYYMM.xlsx`
                    - 支持多个月份文件同时加载
                    - 自动识别文件名中的日期信息

                    ### 2. 文件上传模式
                    - 通过浏览器上传Excel文件
                    - 支持多文件上传
                    - 临时存储，刷新页面后需要重新上传

                    ### 文件格式要求
                    - Excel格式 (.xlsx)
                    - 包含必要的列名
                    """)

            with col2:
                st.markdown("""
                    ## 📊 分析功能

                    ### 核心分析模块
                    1. **绩效概览** - 关键指标汇总
                    2. **收益分布** - 收益分段分析
                    3. **顾问类型分析** - 各类型顾问表现对比
                    4. **大区绩效** - 区域对比分析
                    5. **趋势分析** - 多月份趋势对比
                    6. **会员价值贡献** - 会员价值贡献分析
                    7. **销售利润分析** - 销售利润分布分析

                    ### 详细分析
                    1. **绩效排名** - 自定义排名查看
                    2. **前100vs后100** - 优劣势对比分析
                    3. **区域详情** - 具体区域数据查看
                    4. **区域分析报告** - 区域优劣势详细报告
                    5. **会员价值贡献** - 会员价值贡献详细分析
                    6. **销售利润分析** - 销售利润分布详细分析

                    ### 数据导出
                    - CSV格式数据导出
                    - 筛选后数据下载
                    """)

            # 显示文件格式要求
            with st.expander("📋 详细文件格式要求", expanded=False):
                st.markdown("""
                    ### 必需的数据列

                    请确保Excel文件包含以下列（或类似列名）：

                    | 列名 | 说明 | 示例 |
                    |------|------|------|
                    | 时间/月份 | 数据所属时间 | 2024-01 |
                    | 大区 | 所属大区 | 华北区 |
                    | 区域 | 所属区域 | 北京 |
                    | 门店名称 | 所属门店 | 门店A |
                    | 顾问名称 | 顾问姓名 | 张三 |
                    | 顾问编制 | 顾问类型 | 全职/兼职 |
                    | 最终收益值 | 最终收益金额 | 50000 |
                    | 销售利润 | 销售利润金额 | 45000 |
                    | 新客贡献 | 新客贡献金额 | 5000 |
                    | 会员价值贡献 | 会员价值贡献 | 3000 |
                    | 试饮获客贡献 | 试饮获客贡献 | 2000 |
                    | A+B内码贡献 | 内码贡献金额 | 1000 |
                    | 总收益 | 总收益金额 | 56000 |

                    ### 文件命名规范
                    推荐使用标准命名格式，便于系统自动识别：`利润模型评估报告_原始收益值_YYYYMM.xlsx`""")


    # 注意：main() 函数不应该在这里面

# main() 函数应该在这里，与类同级

if __name__ == "__main__":
    main()
