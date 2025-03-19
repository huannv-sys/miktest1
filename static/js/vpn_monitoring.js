/**
 * VPN Monitoring functionality
 * Handles VPN monitoring view, retrieval and display of VPN connections data
 */
document.addEventListener('DOMContentLoaded', function() {
    // Biến toàn cục
    let refreshInterval = null;
    let vpnTypeChart = null;
    let vpnTrafficChart = null;
    let connectionTrafficChart = null;
    
    // Xử lý chọn thiết bị
    document.getElementById('deviceSelect').addEventListener('change', function() {
        const deviceId = this.value;
        if (deviceId) {
            loadVpnData(deviceId);
        } else {
            // Ẩn tất cả các phần khi không có thiết bị nào được chọn
            document.querySelector('.vpn-summary').classList.add('d-none');
            document.querySelector('.vpn-status').classList.add('d-none');
            document.querySelector('.vpn-connections').classList.add('d-none');
            document.querySelector('.vpn-charts').classList.add('d-none');
        }
    });
    
    // Xử lý nút làm mới
    document.getElementById('btnRefresh').addEventListener('click', function() {
        const deviceId = document.getElementById('deviceSelect').value;
        if (deviceId) {
            loadVpnData(deviceId);
        }
    });
    
    // Xử lý tự động làm mới
    document.querySelectorAll('.refresh-option').forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const interval = parseInt(this.getAttribute('data-interval'));
            
            // Xóa interval hiện tại nếu có
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
            
            // Thiết lập interval mới nếu không phải 0
            if (interval > 0) {
                refreshInterval = setInterval(() => {
                    const deviceId = document.getElementById('deviceSelect').value;
                    if (deviceId) {
                        loadVpnData(deviceId);
                    }
                }, interval * 1000);
                
                // Hiển thị thông báo
                showToast(`Tự động làm mới mỗi ${interval} giây đã được bật`, 'info');
            } else {
                // Hiển thị thông báo
                showToast('Tự động làm mới đã tắt', 'info');
            }
        });
    });
    
    // Xử lý nút xuất dữ liệu
    document.getElementById('btnExport').addEventListener('click', function() {
        const deviceId = document.getElementById('deviceSelect').value;
        if (!deviceId) {
            showToast('Vui lòng chọn một thiết bị trước', 'warning');
            return;
        }
        
        exportVpnData(deviceId);
    });
    
    // Hàm tải dữ liệu VPN
    function loadVpnData(deviceId) {
        // Hiển thị thông báo đang tải
        showLoading();
        
        // Gọi API để lấy dữ liệu VPN
        fetch(`/api/vpn/${deviceId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Không thể kết nối đến thiết bị');
                }
                return response.json();
            })
            .then(data => {
                // Hiển thị các phần dữ liệu VPN
                document.querySelector('.vpn-summary').classList.remove('d-none');
                document.querySelector('.vpn-status').classList.remove('d-none');
                document.querySelector('.vpn-connections').classList.remove('d-none');
                document.querySelector('.vpn-charts').classList.remove('d-none');
                
                // Cập nhật dữ liệu hiển thị
                updateVpnSummary(data);
                updateServerStatus(data.server_config);
                updateVpnConnectionsTable(data.active_connections);
                createOrUpdateVpnCharts(data);
                
                hideLoading();
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Không thể tải dữ liệu VPN: ' + error.message, 'error');
                hideLoading();
            });
    }
    
    // Cập nhật phần tổng quan VPN
    function updateVpnSummary(data) {
        document.getElementById('totalConnections').textContent = data.total_connections;
        document.getElementById('activeConnections').textContent = data.total_connections; // Giả sử tất cả đều đang hoạt động
        
        // Tính tổng lưu lượng (giả sử dữ liệu này sẽ được thêm vào sau)
        let totalRx = 0;
        let totalTx = 0;
        
        if (data.active_connections) {
            data.active_connections.forEach(conn => {
                if (conn.bytes_in) totalRx += parseInt(conn.bytes_in);
                if (conn.bytes_out) totalTx += parseInt(conn.bytes_out);
            });
        }
        
        document.getElementById('totalRx').textContent = formatBytes(totalRx);
        document.getElementById('totalTx').textContent = formatBytes(totalTx);
    }
    
    // Cập nhật trạng thái server VPN
    function updateServerStatus(config) {
        // PPTP Status
        updateServiceStatus('pptp', config.pptp.enabled);
        document.getElementById('pptp-details').textContent = config.pptp.enabled ? 
            `Port: ${config.pptp.port}, Auth: ${config.pptp.authentication.join(', ')}` : 
            'Không kích hoạt';
        
        // L2TP Status
        updateServiceStatus('l2tp', config.l2tp.enabled);
        document.getElementById('l2tp-details').textContent = config.l2tp.enabled ? 
            `Port: ${config.l2tp.port}, Auth: ${config.l2tp.authentication.join(', ')}` : 
            'Không kích hoạt';
        
        // SSTP Status
        updateServiceStatus('sstp', config.sstp.enabled);
        document.getElementById('sstp-details').textContent = config.sstp.enabled ? 
            `Port: ${config.sstp.port}, Auth: ${config.sstp.authentication.join(', ')}` : 
            'Không kích hoạt';
        
        // OpenVPN Status
        updateServiceStatus('ovpn', config.ovpn.enabled);
        document.getElementById('ovpn-details').textContent = config.ovpn.enabled ? 
            `Port: ${config.ovpn.port}, Mode: ${config.ovpn.mode}` : 
            'Không kích hoạt';
    }
    
    // Cập nhật trạng thái dịch vụ
    function updateServiceStatus(service, enabled) {
        const icon = document.getElementById(`${service}-status`);
        if (enabled) {
            icon.classList.add('status-enabled');
            icon.classList.remove('status-disabled');
        } else {
            icon.classList.add('status-disabled');
            icon.classList.remove('status-enabled');
        }
    }
    
    // Cập nhật bảng kết nối VPN
    function updateVpnConnectionsTable(connections) {
        const tableBody = document.getElementById('vpnConnectionsTable');
        tableBody.innerHTML = '';
        
        if (!connections || connections.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="8" class="text-center">Không có kết nối VPN nào đang hoạt động</td>`;
            tableBody.appendChild(row);
            return;
        }
        
        connections.forEach(conn => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${conn.user || 'N/A'}</td>
                <td>${conn.service || conn.type || 'N/A'}</td>
                <td>${conn.address || 'N/A'}</td>
                <td>${conn.local_address || 'N/A'}</td>
                <td>${new Date().toLocaleString()}</td>
                <td>${conn.uptime || 'N/A'}</td>
                <td>${formatBytes(conn.bytes_in || 0)} / ${formatBytes(conn.bytes_out || 0)}</td>
                <td>
                    <button class="btn btn-sm btn-info view-connection" data-id="${conn.id || ''}">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-danger disconnect-connection" data-id="${conn.id || ''}">
                        <i class="bi bi-x-circle"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // Thêm sự kiện cho các nút
        document.querySelectorAll('.view-connection').forEach(btn => {
            btn.addEventListener('click', function() {
                const connId = this.getAttribute('data-id');
                showConnectionDetails(connId);
            });
        });
        
        document.querySelectorAll('.disconnect-connection').forEach(btn => {
            btn.addEventListener('click', function() {
                const connId = this.getAttribute('data-id');
                disconnectVpnConnection(connId);
            });
        });
    }
    
    // Hiển thị chi tiết kết nối
    function showConnectionDetails(connId) {
        const deviceId = document.getElementById('deviceSelect').value;
        if (!deviceId) return;
        
        // Trong thực tế, chúng ta sẽ gọi API để lấy chi tiết kết nối
        // Nhưng hiện tại, sẽ sử dụng mô phỏng
        
        // Hiển thị modal chi tiết kết nối
        const modal = new bootstrap.Modal(document.getElementById('connectionDetailModal'));
        modal.show();
        
        // Mô phỏng dữ liệu chi tiết kết nối
        const connectionInfo = {
            user: 'user1',
            type: 'pptp',
            address: '203.0.113.45',
            local_address: '10.10.10.2',
            uptime: '2h 15m',
            bytes_in: 367001600, // 350 MB
            bytes_out: 125829120, // 120 MB
            encryption: 'mppe128',
            mtu: 1450,
            connected_at: '2025-03-19T08:45:23'
        };
        
        // Cập nhật thông tin kết nối
        const infoTable = document.getElementById('connectionInfoTable');
        infoTable.innerHTML = `
            <tr><th>Tên người dùng:</th><td>${connectionInfo.user}</td></tr>
            <tr><th>Loại kết nối:</th><td>${connectionInfo.type.toUpperCase()}</td></tr>
            <tr><th>Địa chỉ IP nguồn:</th><td>${connectionInfo.address}</td></tr>
            <tr><th>Địa chỉ IP được cấp:</th><td>${connectionInfo.local_address}</td></tr>
            <tr><th>Thời gian kết nối:</th><td>${new Date(connectionInfo.connected_at).toLocaleString()}</td></tr>
        `;
        
        // Cập nhật thông số kết nối
        const statsTable = document.getElementById('connectionStatsTable');
        statsTable.innerHTML = `
            <tr><th>Uptime:</th><td>${connectionInfo.uptime}</td></tr>
            <tr><th>Lưu lượng nhận (Rx):</th><td>${formatBytes(connectionInfo.bytes_in)}</td></tr>
            <tr><th>Lưu lượng gửi (Tx):</th><td>${formatBytes(connectionInfo.bytes_out)}</td></tr>
            <tr><th>Mã hóa:</th><td>${connectionInfo.encryption}</td></tr>
            <tr><th>MTU:</th><td>${connectionInfo.mtu}</td></tr>
        `;
        
        // Tạo biểu đồ lưu lượng
        createConnectionTrafficChart();
        
        // Thêm sự kiện cho nút ngắt kết nối
        document.getElementById('disconnectBtn').onclick = function() {
            disconnectVpnConnection(connId);
            modal.hide();
        };
    }
    
    // Ngắt kết nối VPN
    function disconnectVpnConnection(connId) {
        const deviceId = document.getElementById('deviceSelect').value;
        if (!deviceId) return;
        
        if (confirm('Bạn có chắc chắn muốn ngắt kết nối này?')) {
            // Trong thực tế, chúng ta sẽ gọi API để ngắt kết nối
            // Nhưng hiện tại, sẽ sử dụng mô phỏng
            showToast('Đã ngắt kết nối thành công', 'success');
            
            // Làm mới dữ liệu VPN
            loadVpnData(deviceId);
        }
    }
    
    // Tạo biểu đồ lưu lượng kết nối
    function createConnectionTrafficChart() {
        const ctx = document.getElementById('connectionTrafficChart').getContext('2d');
        
        // Nếu biểu đồ đã tồn tại, hủy nó
        if (connectionTrafficChart) {
            connectionTrafficChart.destroy();
        }
        
        // Mô phỏng dữ liệu thời gian thực
        const timeLabels = [];
        const rxData = [];
        const txData = [];
        
        // Tạo dữ liệu cho 30 phút qua, mỗi phút một điểm
        const now = new Date();
        for (let i = 30; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60000);
            timeLabels.push(time.toLocaleTimeString());
            rxData.push(Math.floor(Math.random() * 500000)); // Random traffic data
            txData.push(Math.floor(Math.random() * 300000)); // Random traffic data
        }
        
        // Tạo biểu đồ mới
        connectionTrafficChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [
                    {
                        label: 'Lưu lượng nhận (Rx)',
                        data: rxData,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderWidth: 2,
                        tension: 0.1
                    },
                    {
                        label: 'Lưu lượng gửi (Tx)',
                        data: txData,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderWidth: 2,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatBytes(value, 1);
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatBytes(context.raw);
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Tạo hoặc cập nhật biểu đồ phân phối VPN
    function createOrUpdateVpnCharts(data) {
        // Biểu đồ phân phối loại kết nối
        const typeCtx = document.getElementById('vpnTypeChart').getContext('2d');
        
        // Dữ liệu cho biểu đồ
        const typeLabels = Object.keys(data.connections_by_type).map(type => type.toUpperCase());
        const typeData = Object.values(data.connections_by_type);
        
        // Các màu cho biểu đồ
        const backgroundColors = [
            'rgba(75, 192, 192, 0.6)',
            'rgba(255, 99, 132, 0.6)',
            'rgba(255, 205, 86, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(153, 102, 255, 0.6)'
        ];
        
        // Nếu biểu đồ đã tồn tại, hủy nó
        if (vpnTypeChart) {
            vpnTypeChart.destroy();
        }
        
        // Tạo biểu đồ mới
        vpnTypeChart = new Chart(typeCtx, {
            type: 'pie',
            data: {
                labels: typeLabels,
                datasets: [{
                    data: typeData,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(color => color.replace('0.6', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Biểu đồ lưu lượng theo thời gian (sẽ được thêm sau khi có dữ liệu thực)
        const trafficCtx = document.getElementById('vpnTrafficChart').getContext('2d');
        
        // Mô phỏng dữ liệu thời gian thực
        const timeLabels = [];
        const rxData = [];
        const txData = [];
        
        // Tạo dữ liệu cho 24 giờ qua, mỗi giờ một điểm
        const now = new Date();
        for (let i = 24; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 3600000);
            timeLabels.push(time.toLocaleTimeString());
            rxData.push(Math.floor(Math.random() * 5000000)); // Random traffic data
            txData.push(Math.floor(Math.random() * 3000000)); // Random traffic data
        }
        
        // Nếu biểu đồ đã tồn tại, hủy nó
        if (vpnTrafficChart) {
            vpnTrafficChart.destroy();
        }
        
        // Tạo biểu đồ mới
        vpnTrafficChart = new Chart(trafficCtx, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [
                    {
                        label: 'Lưu lượng vào',
                        data: rxData,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderWidth: 2,
                        tension: 0.1
                    },
                    {
                        label: 'Lưu lượng ra',
                        data: txData,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderWidth: 2,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatBytes(value, 1);
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatBytes(context.raw);
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Hàm xuất dữ liệu VPN
    function exportVpnData(deviceId) {
        // Trong thực tế, chúng ta sẽ gọi API để lấy dữ liệu xuất
        // Nhưng hiện tại, sẽ sử dụng mô phỏng
        
        fetch(`/api/vpn/${deviceId}/export`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Không thể xuất dữ liệu');
                }
                return response.json();
            })
            .then(data => {
                // Tạo file CSV từ dữ liệu
                let csvContent = "data:text/csv;charset=utf-8,";
                
                // Header
                csvContent += "User,Type,Source IP,Assigned IP,Connected At,Uptime,Rx,Tx\n";
                
                // Rows
                data.connections.forEach(conn => {
                    csvContent += `${conn.user || 'N/A'},`;
                    csvContent += `${conn.service || conn.type || 'N/A'},`;
                    csvContent += `${conn.address || 'N/A'},`;
                    csvContent += `${conn.local_address || 'N/A'},`;
                    csvContent += `${new Date().toLocaleString()},`;
                    csvContent += `${conn.uptime || 'N/A'},`;
                    csvContent += `${formatBytes(conn.bytes_in || 0)},`;
                    csvContent += `${formatBytes(conn.bytes_out || 0)}\n`;
                });
                
                // Download file
                const encodedUri = encodeURI(csvContent);
                const link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                link.setAttribute("download", `vpn_connections_${deviceId}_${new Date().toISOString().slice(0,10)}.csv`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                showToast('Đã xuất dữ liệu thành công', 'success');
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Không thể xuất dữ liệu: ' + error.message, 'error');
            });
    }
    
    // Helper function: Hiển thị loading
    function showLoading() {
        // Thêm lớp loading cho container
        document.querySelector('.container').classList.add('loading');
    }
    
    // Helper function: Ẩn loading
    function hideLoading() {
        // Xóa lớp loading cho container
        document.querySelector('.container').classList.remove('loading');
    }
    
    // Helper function: Hiển thị thông báo
    function showToast(message, type = 'info') {
        // Sử dụng Bootstrap toast nếu có
        if (typeof bootstrap !== 'undefined') {
            const toastEl = document.createElement('div');
            toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
            toastEl.setAttribute('role', 'alert');
            toastEl.setAttribute('aria-live', 'assertive');
            toastEl.setAttribute('aria-atomic', 'true');
            toastEl.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
            
            document.body.appendChild(toastEl);
            const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
            toast.show();
            
            // Xóa toast sau khi ẩn
            toastEl.addEventListener('hidden.bs.toast', function() {
                toastEl.remove();
            });
        } else {
            // Fallback nếu không có Bootstrap
            alert(message);
        }
    }
    
    // Helper function: Định dạng bytes
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
});
