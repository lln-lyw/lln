#!/bin/bash
echo "🏥 启动服务器健康监测系统..."
echo "📦 检查Docker环境..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 未找到Docker，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 未找到Docker Compose，请先安装Docker Compose"
    exit 1
fi

echo "🔧 构建Docker镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

echo "⏳ 等待服务启动..."
sleep 5

echo "✅ 系统启动成功！"
echo "🌐 请在浏览器访问：http://localhost:5000"
echo ""
echo "📊 系统功能："
echo "   • 多服务器实时监控"
echo "   • 可视化图表显示"
echo "   • 自动告警功能"
echo "   • 历史数据查询"
echo ""
echo "🔧 管理命令："
echo "   停止系统: docker-compose down"
echo "   查看日志: docker-compose logs"
echo "   重启系统: docker-compose restart"
