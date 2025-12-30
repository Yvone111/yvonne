import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
import warnings
from datetime import datetime, timedelta
import sys

# 添加自定义模块路径（如果需要）
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
</style>
""", unsafe_allow_html=True)


class NutritionAdviserDashboard:
    def __init__(self, data_folder=None):
        """
        营养顾问绩效评估仪表板
        data_folder: 包含月度Excel报告文件的文件夹路径
        """
        # 设置默认数据文件夹路径
        if data_folder is None:
            # 默认路径 - 根据您的需求修改
            self.data_folder = "/Users/Yvonne/Desktop/伊利/人效分析/营养顾问分析报告"
        else:
            self.data_folder = data_folder

        self.monthly_data = {}
        self.uploaded_data = {}  # 新增：存储上传文件的数据
        self.load_monthly_data()

    def load_monthly_data(self):
        """加载所有月份的Excel报告数据"""
        # 检查文件夹是否存在
        if not os.path.exists(self.data_folder):
            st.sidebar.error(f"数据文件夹不存在: {self.data_folder}")
            st.sidebar.info("请使用上传功能添加Excel文件")
            return

        # 查找所有符合命名模式的Excel文件
        pattern = os.path.join(self.data_folder, "利润模型评估报告_原始收益值_*.xlsx")
        excel_files = glob.glob(pattern)

        if not excel_files:
            st.sidebar.warning(f"在 {self.data_folder} 中没有找到Excel文件")
            st.sidebar.info("请确保文件命名格式为: 利润模型评估报告_原始收益值_YYYYMM.xlsx")
            return

        st.sidebar.info(f"找到 {len(excel_files)} 个本地Excel文件")

        for file_path in excel_files:
            try:
                # 从文件名提取月份信息
                filename = os.path.basename(file_path)

                # 假设文件名格式: 利润模型评估报告_原始收益值_YYYYMM.xlsx
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
                        df['数据来源'] = '本地文件'  # 标记数据来源

                        # 存储数据
                        self.monthly_data[month_key] = {
                            'data': df,
                            'date': file_date,
                            'file_path': file_path,
                            'source': 'local'
                        }

                        st.sidebar.success(f"已加载本地文件: {month_key}")

                    except ValueError as e:
                        st.sidebar.warning(f"文件名日期格式不正确 {filename}: {str(e)}")

            except Exception as e:
                st.sidebar.error(f"加载文件失败 {file_path}: {str(e)}")

    def load_uploaded_files(self, uploaded_files):
        """处理上传的文件 - 新增方法"""
        if not uploaded_files:
            return

        for uploaded_file in uploaded_files:
            try:
                # 从文件名提取月份信息
                filename = uploaded_file.name
                month_key = self.extract_month_from_filename(filename)
                
                # 读取Excel文件
                df = pd.read_excel(uploaded_file)
                
                # 添加月份标识列
                df['月份'] = month_key
                df['日期'] = datetime.now()
                df['数据来源'] = '上传文件'  # 标记数据来源
                
                # 存储到上传数据字典
                self.uploaded_data[month_key] = {
                    'data': df,
                    'date': datetime.now(),
                    'file_path': f"上传文件: {filename}",
                    'source': 'uploaded'
                }
                
                st.sidebar.success(f"✅ 已加载上传文件: {month_key} (共{len(df)}条记录)")
                
            except Exception as e:
                st.sidebar.error(f"❌ 处理上传文件 {uploaded_file.name} 时出错: {str(e)}")

    def extract_month_from_filename(self, filename):
        """从文件名提取月份信息"""
        # 支持多种文件名格式
        if "利润模型评估报告_原始收益值_" in filename:
            date_str = filename.replace("利润模型评估报告_原始收益值_", "").replace(".xlsx", "")
        elif "利润模型评估报告_" in filename:
            date_str = filename.replace("利润模型评估报告_", "").replace(".xlsx", "")
        else:
            # 如果无法解析，使用文件名（不含扩展名）
            date_str = filename.replace(".xlsx", "")
        
        # 尝试解析日期
        try:
            if len(date_str) == 6 and date_str.isdigit():
                file_date = datetime.strptime(date_str, "%Y%m")
                return file_date.strftime("%Y年%m月")
        except ValueError:
            pass
            
        return filename.replace(".xlsx", "")

    def get_all_data(self):
        """获取所有数据（本地+上传）"""
        all_data = {}
        all_data.update(self.monthly_data)  # 本地数据
        all_data.update(self.uploaded_data)  # 上传数据
        return all_data

    def get_available_months(self):
        """获取可用的月份列表（包括本地和上传的）"""
        all_data = self.get_all_data()
        if not all_data:
            return []
        return sorted(all_data.keys(),
                      key=lambda x: all_data[x]['date'],
                      reverse=True)

    def get_month_data(self, month):
        """获取指定月份的数据（优先使用上传的数据）"""
        # 优先检查上传的数据
        if month in self.uploaded_data:
            return self.uploaded_data[month]['data']
        elif month in self.monthly_data:
            return self.monthly_data[month]['data']
        else:
            return pd.DataFrame()

    def get_previous_month(self, current_month):
        """获取上一个月份的数据"""
        months = self.get_available_months()
        if not months or current_month not in months:
            return None

        current_index = months.index(current_month)
        if current_index < len(months) - 1:
            return months[current_index + 1]  # 因为是倒序排列
        return None

    # 保留您原有的所有方法不变
    def create_overview_dashboard(self, selected_month):
        """创建概览仪表板"""
        st.header(f"📊 营养顾问绩效评估概览 - {selected_month}")

        df = self.get_month_data(selected_month)
        if df.empty:
            st.warning(f"没有找到 {selected_month} 的数据")
            return

        # 显示数据来源
        data_source = "上传文件" if selected_month in self.uploaded_data else "本地文件"
        st.caption(f"数据来源: {data_source}")

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
            if len(self.get_all_data()) > 1:
                self.create_trend_analysis_chart(selected_month)
            else:
                st.info("需要多个月份数据才能显示趋势分析")

    # 保留您原有的所有图表方法不变
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
        """创建顾问类型分析图表 - 改进版本：使用go.Figure创建堆叠条形图"""
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

        # 显示详细统计表 - 销售利润坎级统计
        st.subheader("各类型顾问销售利润分布")

        # 检查是否有销售利润列
        if '销售利润' not in df.columns:
            st.warning("没有销售利润数据")
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
        st.dataframe(sales_summary, use_container_width=True)

        # 使用go.Figure创建堆叠条形图
        st.subheader("销售利润分布可视化")
        self.create_stacked_bar_chart(sales_distribution, month)

    def create_stacked_bar_chart(self, sales_distribution, month):
        """使用go.Figure创建堆叠条形图，并将数值标注放在柱形右侧"""
        # 获取顾问类型和坎级标签
        adviser_types = sales_distribution.index.tolist()
        sales_labels = sales_distribution.columns.tolist()

        # 创建图形
        fig = go.Figure()

        # 定义颜色
        colors = ['#8dd3c7', '#ffffb4', '#bebadb', '#fb8072']

        # 为每个坎级添加一个条形图轨迹
        for i, label in enumerate(sales_labels):
            y_data = sales_distribution[label]
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
                hovertemplate=f"<b>{label}</b><br>顾问类型: %{x}<br>人数: %{y}<br><extra></extra>"
            ))

        # 更新布局
        fig.update_layout(
            title=dict(text=f"{month} 各类型顾问销售利润分布", font=dict(size=18)),
            xaxis=dict(title="顾问类型", title_font=dict(size=14), tickfont=dict(size=12)),
            yaxis=dict(title="人数", title_font=dict(size=14), tickfont=dict(size=12)),
            barmode='stack', height=500, showlegend=True,
            margin=dict(l=50, r=50, t=80, b=50), uniformtext_minsize=12
        )

        # 确保y轴有足够的空间显示外部文本
        max_value = sales_distribution.sum(axis=1).max()
        fig.update_yaxes(range=[0, max_value * 1.15])

        st.plotly_chart(fig, use_container_width=True)

    def create_region_analysis_chart(self, df, month):
        """创建大区分析图表"""
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

        # 创建水平条形图
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
            yaxis_title="大区", xaxis_title="平均收益（元）", height=400, showlegend=False
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

        all_data = self.get_all_data()
        if len(all_data) < 2:
            st.info("需要至少两个月份的数据才能进行趋势分析")
            return

        # 准备趋势数据
        trend_data = []
        for month, data_info in all_data.items():
            df = data_info['data']
            if '最终收益值' in df.columns:
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

        # 创建趋势图
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df['月份'], y=trend_df['总体平均收益'],
            mode='lines+markers', name='总体平均', line=dict(width=4)
        ))

        fig.update_layout(
            title="各月份收益趋势", xaxis_title="月份", yaxis_title="平均收益（元）",
            height=400, showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    # 保留您原有的其他所有方法...
    # [这里包含您原有的所有其他方法，包括create_region_strengths_weaknesses, create_performance_comparison等]

    def create_performance_comparison(self, df, month):
        """创建前100名与后100名营养顾问的优劣势分析"""
        # 您原有的完整代码保持不变
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
        comparison_df['前100名优势百分比'] = ((comparison_df['前100名平均值'] - comparison_df['后100名平均值']) / comparison_df['后100名平均值'] * 100).round(1)
        comparison_df = comparison_df.fillna(0)

        # 显示关键指标对比
        st.subheader("📊 关键指标对比")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("前100名平均收益", f"¥{top_100['最终收益值'].mean():,.0f}")
        with col2:
            st.metric("后100名平均收益", f"¥{bottom_100['最终收益值'].mean():,.0f}")
        with col3:
            advantage = ((top_100['最终收益值'].mean() - bottom_100['最终收益值'].mean()) / bottom_100['最终收益值'].mean() * 100)
            st.metric("前100名优势", f"{advantage:.1f}%")

        # 创建对比条形图
        fig = px.bar(
            comparison_df, x='指标', y=['前100名平均值', '后100名平均值', '全量平均值'],
            title=f"{month} 前100名 vs 后100名 关键指标对比", barmode='group',
            labels={'value': '平均值', 'variable': '分组'}, text_auto='.0f'
        )
        fig.update_layout(xaxis_title="指标", yaxis_title="平均值（元）", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # 显示详细对比表格
        st.subheader("📋 详细对比数据")
        display_df = comparison_df.copy()
        for col in ['前100名平均值', '后100名平均值', '全量平均值']:
            display_df[col] = display_df[col].apply(lambda x: f"¥{x:,.0f}" if pd.notnull(x) else "¥0")
        display_df['前100名优势百分比'] = display_df['前100名优势百分比'].apply(lambda x: f"{x:+.1f}%")
        st.dataframe(display_df, use_container_width=True)


def main():
    """主函数"""
    st.title("🏢 营养顾问绩效评估系统")
    st.markdown("---")

    # 侧边栏 - 文件上传和月份选择
    st.sidebar.title("📁 数据管理")

    # 设置数据文件夹路径
    data_folder = "/Users/Yvonne/Desktop/伊利/人效分析/营养顾问分析报告"

    # 创建仪表板实例
    dashboard = NutritionAdviserDashboard(data_folder)

    # 文件上传功能 - 作为补充选项
    st.sidebar.subheader("📤 文件上传功能")
    uploaded_files = st.sidebar.file_uploader(
        "上传Excel文件（补充或覆盖本地数据）",
        type=["xlsx"],
        accept_multiple_files=True,
        help="请上传利润模型评估报告Excel文件。上传的文件将优先于本地文件显示。"
    )

    # 处理上传的文件
    if uploaded_files:
        dashboard.load_uploaded_files(uploaded_files)

    # 月份选择器
    available_months = dashboard.get_available_months()
    
    # 显示数据来源统计
    local_count = len(dashboard.monthly_data)
    uploaded_count = len(dashboard.uploaded_data)
    st.sidebar.info(f"📊 数据统计: 本地{local_count}个月, 上传{uploaded_count}个月")

    if available_months:
        selected_month = st.sidebar.selectbox(
            "选择查看月份",
            options=available_months,
            index=0
        )

        # 获取上月数据
        previous_month = dashboard.get_previous_month(selected_month)

        # 显示数据概览
        dashboard.create_overview_dashboard(selected_month)

        # 添加详细数据选项卡
        st.markdown("---")
        st.header("📋 详细数据查看")

        tab1, tab2, tab3, tab4 = st.tabs(["原始数据", "绩效排名", "前100vs后100分析", "区域详情"])

        with tab1:
            df = dashboard.get_month_data(selected_month)
            if not df.empty:
                # 显示数据来源信息
                data_source = "上传文件" if selected_month in dashboard.uploaded_data else "本地文件"
                st.subheader(f"{selected_month} - 原始数据 [来源: {data_source}]")
                
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
            df = dashboard.get_month_data(selected_month)
            if not df.empty and '最终收益值' in df.columns:
                # 添加排名选项 - 使用3列布局
                col1, col2, col3 = st.columns(3)
                with col1:
                    rank_by = st.selectbox("排名依据", options=["最终收益值", "销售利润", "总收益"], index=0)
                with col2:
                    rank_type = st.selectbox("排名类型", options=["前N名", "后N名"], index=0)
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
                for col in ['顾问名称', '顾问编制', '大区', '区域', '门店名称', '最终收益值', '销售利润', '总收益']:
                    if col in ranked_df.columns:
                        display_columns.append(col)

                ranked_df = ranked_df[display_columns]
                ranked_df['排名'] = range(1, len(ranked_df) + 1)
                cols = ['排名'] + [col for col in ranked_df.columns if col != '排名']
                ranked_df = ranked_df[cols]

                st.dataframe(ranked_df, use_container_width=True)
            else:
                st.warning("没有排名数据可显示")

        with tab3:
            df = dashboard.get_month_data(selected_month)
            if not df.empty and '最终收益值' in df.columns:
                dashboard.create_performance_comparison(df, selected_month)
            else:
                st.warning("没有足够的数据进行对比分析")

        with tab4:
            df = dashboard.get_month_data(selected_month)
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
                        fig = px.pie(values=type_dist.values, names=type_dist.index, 
                                   title=f"{selected_region} 顾问类型分布")
                        st.plotly_chart(fig, use_container_width=True)

                    # 显示该区域详细数据
                    st.subheader("详细数据")
                    st.dataframe(region_data, use_container_width=True)
                else:
                    st.warning(f"没有找到 {selected_region} 的数据")
            else:
                st.warning("没有区域数据可显示")

    else:
        st.info("👈 请确保数据文件夹中有Excel文件，或通过侧边栏上传文件")

        # 显示使用说明
        st.markdown("""
        ## 使用说明

        1. **数据加载**: 应用会自动从指定文件夹加载Excel文件
        2. **文件上传**: 可通过侧边栏上传Excel文件作为补充或覆盖
        3. **文件格式**: 文件命名格式应为: `利润模型评估报告_原始收益值_YYYYMM.xlsx`
        4. **数据优先级**: 上传的文件优先于本地文件显示

        ## 文件格式要求

        请确保Excel文件包含以下列（或类似列名）：
        - 时间/月份
        - 大区
        - 区域
        - 门店名称
        - 顾问名称
        - 顾问编制
        - 最终收益值
        - 销售利润
        - 新客贡献
        - 会员价值贡献
        - 试饮获客贡献
        - A+B内码贡献
        - 总收益
        """)


if __name__ == "__main__":
    main()
