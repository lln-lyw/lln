from flask import Flask, request, render_template, jsonify
import json
import os
import paramiko  # 新增：用于SSH连接
import re        # 新增：用于处理文本
import datetime  # 新增：用于时间处理
import csv       # 新增：用于保存历史数据

app = Flask(__name__)

# 数据存储文件
DATA_FILE = 'data/hosts.json'

# 确保数据目录存在
os.makedirs('data', exist_ok=True)

@app.route('/')
def index():
    """主页面 - 就像医院的接待台"""
    return '''
    <html>
    <head>
        <title>服务器健康监测系统</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                color: #333;
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .form-box {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 25px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .form-box h3 {
                margin-bottom: 15px;
            }
            .form-box input {
                padding: 12px;
                margin: 8px 5px;
                border: none;
                border-radius: 5px;
                width: 200px;
                font-size: 16px;
            }
            .form-box button {
                background: #4CAF50;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 10px;
            }
            .form-box button:hover {
                background: #45a049;
            }
            .card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 4px solid #667eea;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
                font-size: 14px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            .status-normal { 
                color: green; 
                font-weight: bold;
            }
            .status-error { 
                color: red; 
                font-weight: bold;
            }
            .alert-danger {
                background: #f8d7da;
                color: #721c24;
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
                border-left: 4px solid #dc3545;
            }
            .alert-warning {
                background: #fff3cd;
                color: #856404;
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
                border-left: 4px solid #ffc107;
            }
            .alert-success {
                background: #d1edff;
                color: #004085;
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
            .charts-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin: 20px 0;
            }
            .chart-box {
                flex: 1;
                min-width: 300px;
                background: white;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .chart-title {
                text-align: center;
                margin-bottom: 15px;
                font-size: 1.2em;
                color: #333;
            }
            .chart {
                height: 300px;
                width: 100%;
            }
            .btn {
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            .btn-danger {
                background: #dc3545;
                color: white;
            }
            .btn-info {
                background: #17a2b8;
                color: white;
                margin-left: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 服务器健康监测系统</h1>
                <p>实时监控您的服务器健康状况</p>
            </div>
            
            <div class="form-box">
                <h3>➕ 添加要监测的服务器</h3>
                <form action="/add_host" method="post">
                    服务器IP：<input type="text" name="ip" placeholder="例如：192.168.1.100" required>
                    用户名：<input type="text" name="user" value="root" required>
                    密码：<input type="password" name="password" required>
                    <button type="submit">添加服务器</button>
                </form>
            </div>

            <!-- 告警面板 -->
            <div class="card">
                <h3>🔔 系统告警</h3>
                <div id="alerts-container">
                    <div class="alert-success">✅ 系统正在运行，等待添加服务器...</div>
                </div>
            </div>

            <div class="charts-container">
                <div class="chart-box">
                    <div class="chart-title">📈 CPU使用率监控</div>
                    <div id="cpu-chart" class="chart"></div>
                </div>
                <div class="chart-box">
                    <div class="chart-title">💾 内存使用率监控</div>
                    <div id="memory-chart" class="chart"></div>
                </div>
            </div>

            <div class="card">
                <h3>📋 已监测的服务器列表</h3>
                <div id="host-list">
                    <p>暂无服务器，请在上方添加服务器。</p>
                </div>
            </div>

            <div class="card">
                <h3>📊 实时健康数据</h3>
                <div id="monitor-data">
                    <p>等待数据更新...</p>
                </div>
            </div>
        </div>

        <!-- 引入ECharts图表库 -->
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>

        <script>
            // 初始化图表
            const cpuChart = echarts.init(document.getElementById('cpu-chart'));
            const memoryChart = echarts.init(document.getElementById('memory-chart'));

            // 图表基础配置
            const chartOption = {
                tooltip: {
                    trigger: 'axis',
                    formatter: '{b}: {c}%'
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: [],
                    axisLabel: {
                        rotate: 45
                    }
                },
                yAxis: {
                    type: 'value',
                    max: 100,
                    axisLabel: {
                        formatter: '{value}%'
                    }
                },
                series: [{
                    type: 'bar',
                    data: [],
                    itemStyle: {
                        color: function(params) {
                            // 根据数值显示不同颜色
                            const value = params.value;
                            if (value > 80) return '#ff4d4f';
                            if (value > 60) return '#faad14';
                            return '#52c41a';
                        }
                    }
                }]
            };

            cpuChart.setOption(chartOption);
            memoryChart.setOption(chartOption);

            // 更新所有数据
            function updateData() {
                fetch('/api/monitor_data')
                    .then(response => response.json())
                    .then(data => {
                        updateHostList(data.hosts);
                        updateMonitorTable(data.metrics);
                        updateCharts(data.metrics);
                        updateAlerts(data.alerts || []);
                    })
                    .catch(error => {
                        console.error('更新数据失败:', error);
                    });
            }

            // 更新服务器列表
            function updateHostList(hosts) {
                const container = document.getElementById('host-list');
                if (hosts.length === 0) {
                    container.innerHTML = '<p>暂无服务器，请在上方添加服务器。</p>';
                    return;
                }

                let html = '<table><tr><th>IP地址</th><th>用户名</th><th>操作</th></tr>';
                hosts.forEach(host => {
                    html += `<tr>
                        <td>${host.ip}</td>
                        <td>${host.user}</td>
                        <td>
                            <button class="btn btn-danger" onclick="deleteHost('${host.ip}')">删除</button>
                            <button class="btn btn-info" onclick="viewHistory('${host.ip}')">历史</button>
                        </td>
                    </tr>`;
                });
                html += '</table>';
                container.innerHTML = html;
            }

            // 更新监控表格
            function updateMonitorTable(metrics) {
                const container = document.getElementById('monitor-data');
                if (metrics.length === 0) {
                    container.innerHTML = '<p>暂无监控数据。</p>';
                    return;
                }

                let html = '<table><tr><th>服务器IP</th><th>状态</th><th>CPU使用率</th><th>内存使用率</th><th>检查时间</th></tr>';
                metrics.forEach(metric => {
                    const statusClass = metric.status === '正常' ? 'status-normal' : 'status-error';
                    html += `<tr>
                        <td>${metric.ip}</td>
                        <td class="${statusClass}">${metric.status}</td>
                        <td>${metric.cpu}</td>
                        <td>${metric.memory}</td>
                        <td>${metric.timestamp}</td>
                    </tr>`;
                });
                html += '</table>';
                container.innerHTML = html;
            }

            // 更新图表
            function updateCharts(metrics) {
                const ips = metrics.map(m => m.ip);
                const cpuData = metrics.map(m => {
                    const cpuStr = m.cpu.replace('%', '').replace('连接失败', '0');
                    return parseFloat(cpuStr) || 0;
                });
                const memoryData = metrics.map(m => {
                    const memoryStr = m.memory.replace('%', '').replace('连接失败', '0');
                    return parseFloat(memoryStr) || 0;
                });

                cpuChart.setOption({
                    xAxis: { data: ips },
                    series: [{ data: cpuData }]
                });

                memoryChart.setOption({
                    xAxis: { data: ips },
                    series: [{ data: memoryData }]
                });
            }

            // 更新告警信息
            function updateAlerts(alerts) {
                const container = document.getElementById('alerts-container');
                if (alerts.length === 0) {
                    container.innerHTML = '<div class="alert-success">✅ 一切正常，所有服务器运行良好</div>';
                    return;
                }

                let html = '';
                alerts.forEach(alert => {
                    const alertClass = alert.level === 'danger' ? 'alert-danger' : 'alert-warning';
                    html += `<div class="${alertClass}">
                        <strong>${alert.type}</strong>: ${alert.message} (${alert.time})
                    </div>`;
                });
                container.innerHTML = html;
            }

            // 删除服务器
            function deleteHost(ip) {
                if (confirm('确定要删除服务器 ' + ip + ' 吗？')) {
                    fetch('/delete_host', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ip: ip})
                    }).then(() => {
                        updateData(); // 重新加载数据
                    });
                }
            }

            // 查看历史数据
            function viewHistory(ip) {
                window.open('/history/' + ip, '_blank');
            }

            // 页面加载时立即更新，然后每5秒更新一次
            updateData();
            setInterval(updateData, 5000);

            // 窗口大小变化时重绘图表
            window.addEventListener('resize', function() {
                cpuChart.resize();
                memoryChart.resize();
            });
        </script>
    </body>
    </html>
    '''

@app.route('/add_host', methods=['POST'])
def add_host():
    """添加服务器 - 就像登记病人"""
    ip = request.form['ip']
    user = request.form['user']
    password = request.form['password']
    
    # 读取现有数据
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except:
        data = {'hosts': []}
    
    # 检查是否已存在
    for host in data['hosts']:
        if host['ip'] == ip:
            return '服务器已存在！<a href="/">返回首页</a>'
    
    # 添加新服务器
    data['hosts'].append({
        'ip': ip,
        'user': user,
        'password': password
        'added_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # 保存数据
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)
    
    return '服务器添加成功！<a href="/">返回首页</a>'

@app.route('/delete_host', methods=['POST'])
def delete_host():
    """删除服务器"""
    ip_to_delete = request.json['ip']
    
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        
        # 过滤掉要删除的服务器
        data['hosts'] = [host for host in data['hosts'] if host['ip'] != ip_to_delete]
        
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
        
        return jsonify({'status': 'success'})
    except:
        return jsonify({'status': 'error'})

def get_real_metrics(host):
    """真实连接服务器获取监控数据"""
    try:
        print(f"🔍 尝试连接服务器: {host['ip']}")
        
        # 创建SSH连接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 设置连接参数
        ssh.connect(
            host['ip'], 
            username=host['user'], 
            password=host['password'], 
            timeout=10,
            banner_timeout=10
        )
        
        print(f"✅ SSH连接成功: {host['ip']}")
        
        # 获取CPU使用率 - 使用更兼容的命令
        stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | head -1")
        cpu_output = stdout.read().decode()
        
        cpu_used = "未知"
        if 'Cpu(s)' in cpu_output:
            cpu_match = re.search(r'(\d+\.\d+)%? id', cpu_output)
            if cpu_match:
                cpu_idle = float(cpu_match.group(1))
                cpu_used = f"{100 - cpu_idle:.1f}%"
        else:
            # 备用方法：使用 /proc/stat
            stdin, stdout, stderr = ssh.exec_command("head -n1 /proc/stat")
            cpu_line = stdout.read().decode()
            cpu_numbers = re.findall(r'\d+', cpu_line)
            if len(cpu_numbers) >= 8:
                total_time = sum(int(x) for x in cpu_numbers[1:8])
                idle_time = int(cpu_numbers[4])
                cpu_used = f"{(1 - idle_time/total_time) * 100:.1f}%" if total_time > 0 else "0%"
        
        # 获取内存使用率 - 使用更简单的命令
        stdin, stdout, stderr = ssh.exec_command("free | grep Mem:")
        mem_output = stdout.read().decode()
        
        mem_used = "未知"
        mem_numbers = re.findall(r'\d+', mem_output)
        if len(mem_numbers) >= 2:
            total_mem = int(mem_numbers[0])
            used_mem = int(mem_numbers[1])
            mem_used = f"{(used_mem/total_mem)*100:.1f}%" if total_mem > 0 else "0%"
        
        ssh.close()
        print(f"✅ 数据采集成功: {host['ip']} - CPU: {cpu_used}, 内存: {mem_used}")
        return cpu_used, mem_used
        
    except Exception as e:
        print(f"❌ 连接失败 {host['ip']}: {str(e)}")
        return "连接失败", "连接失败"

def check_alerts(metrics):
    """检查告警条件"""
    alerts = []
    for metric in metrics:
        # 尝试提取数字值
        cpu_str = metric['cpu'].replace('%', '').replace('连接失败', '0')
        memory_str = metric['memory'].replace('%', '').replace('连接失败', '0')
        
        try:
            cpu_value = float(cpu_str)
            memory_value = float(memory_str)
        except:
            cpu_value = 0
            memory_value = 0
        
        if cpu_value > 80:
            alerts.append({
                'type': '⚠️ CPU告警',
                'message': f"服务器 {metric['ip']} CPU使用率过高: {metric['cpu']}",
                'level': 'danger',
                'time': datetime.datetime.now().strftime("%H:%M:%S")
            })
        
        if memory_value > 85:
            alerts.append({
                'type': '🚨 内存告警', 
                'message': f"服务器 {metric['ip']} 内存使用率过高: {metric['memory']}",
                'level': 'warning',
                'time': datetime.datetime.now().strftime("%H:%M:%S")
            })
    
    return alerts

def save_history_data(metric):
    """保存历史数据到CSV文件"""
    history_file = f"data/history_{metric['ip'].replace('.', '_')}.csv"
    file_exists = os.path.isfile(history_file)
    
    with open(history_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['时间', 'CPU使用率', '内存使用率', '状态'])
        
        writer.writerow([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            metric['cpu'],
            metric['memory'], 
            metric.get('status', '正常')
        ])

@app.route('/api/monitor_data')
def get_monitor_data():
    """获取监控数据 - 这个路由函数之前缺失了！"""
    try:
        # 读取服务器列表
        with open(DATA_FILE, 'r') as f:
            hosts_data = json.load(f)
        
        metrics = []
        for host in hosts_data['hosts']:
            # 使用真实的数据采集
            cpu, memory = get_real_metrics(host)
            metric_data = {
                'ip': host['ip'],
                'cpu': cpu,
                'memory': memory,
                'status': '正常' if '连接失败' not in cpu else '异常',
                'timestamp': datetime.datetime.now().strftime("%H:%M:%S")
            }
            metrics.append(metric_data)
            
            # 保存历史数据
            save_history_data(metric_data)
        
        # 检查告警
        alerts = check_alerts(metrics)
        
        return jsonify({
            'hosts': hosts_data['hosts'],
            'metrics': metrics,
            'alerts': alerts
        })
    except Exception as e:
        print(f"❌ 获取监控数据错误: {e}")
        return jsonify({'hosts': [], 'metrics': [], 'alerts': []})

@app.route('/history/<ip>')
def show_history(ip):
    """显示历史数据页面"""
    history_file = f"data/history_{ip.replace('.', '_')}.csv"
    
    # 读取历史数据
    history_data = []
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过标题行
            for row in reader:
                if len(row) >= 4:
                    history_data.append({
                        'time': row[0],
                        'cpu': row[1],
                        'memory': row[2],
                        'status': row[3]
                    })
    
    # 只显示最近50条记录
    recent_data = history_data[-50:]
    
    return f'''
    <html>
    <head>
        <title>历史数据 - {ip}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .back-btn {{ background: #007bff; color: white; padding: 10px 20px; 
                       text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <a href="/" class="back-btn">← 返回首页</a>
        <h2>📊 服务器 {ip} 历史数据</h2>
        
        <table>
            <tr>
                <th>时间</th>
                <th>CPU使用率</th>
                <th>内存使用率</th>
                <th>状态</th>
            </tr>
            {"".join(f'<tr><td>{data["time"]}</td><td>{data["cpu"]}</td><td>{data["memory"]}</td><td>{data["status"]}</td></tr>' 
                    for data in reversed(recent_data))}
        </table>
        
        <p>共 {len(recent_data)} 条记录（显示最近50条）</p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
