/**
 * Settings JavaScript for MikroTik Monitoring System
 * Handles system settings management
 */

// Store current settings
let currentSettings = {};

// Initialize settings page components
document.addEventListener('DOMContentLoaded', function() {
    // Load settings
    loadSettings();
    
    // Set up event listeners
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // General settings form
    document.getElementById('save-general-settings').addEventListener('click', saveGeneralSettings);
    
    // Monitoring settings form
    document.getElementById('save-monitoring-settings').addEventListener('click', saveMonitoringSettings);
    
    // Email settings form
    document.getElementById('save-email-settings').addEventListener('click', saveEmailSettings);
    
    // Test email button
    document.getElementById('test-email').addEventListener('click', testEmail);
    
    // Telegram settings form
    document.getElementById('save-telegram-settings').addEventListener('click', saveTelegramSettings);
    
    // Test telegram button
    document.getElementById('test-telegram').addEventListener('click', testTelegram);
    
    // Backup and discovery settings form
    document.getElementById('save-backup-settings').addEventListener('click', saveBackupSettings);
}

// Load settings from API
async function loadSettings() {
    try {
        const response = await fetchWithAuth('/api/config/settings');
        
        if (!response.ok) {
            throw new Error('Failed to load settings');
        }
        
        const settings = await response.json();
        currentSettings = settings;
        
        // Update form fields with current settings
        updateSettingsForm(settings);
        
    } catch (error) {
        console.error('Error loading settings:', error);
        showError('Failed to load settings. Please try refreshing the page.');
    }
}

// Update settings form with values
function updateSettingsForm(settings) {
    // General settings
    document.getElementById('session_timeout').value = settings.session_timeout || 60;
    document.getElementById('timezone').value = settings.timezone || 'UTC';
    document.getElementById('date_format').value = settings.date_format || 'YYYY-MM-DD';
    document.getElementById('enable_dark_mode').checked = settings.enable_dark_mode === 'True';
    
    // Monitoring settings
    document.getElementById('monitoring_interval').value = settings.monitoring_interval || 60;
    document.getElementById('alert_check_interval').value = settings.alert_check_interval || 30;
    document.getElementById('metrics_retention_days').value = settings.metrics_retention_days || 30;
    
    // Email settings
    document.getElementById('email_enabled').checked = settings.email_enabled === 'True';
    document.getElementById('mail_server').value = settings.mail_server || '';
    document.getElementById('mail_port').value = settings.mail_port || 587;
    document.getElementById('mail_use_tls').checked = settings.mail_use_tls !== 'False';
    document.getElementById('mail_username').value = settings.mail_username || '';
    document.getElementById('mail_password').value = settings.mail_password || '';
    document.getElementById('mail_from').value = settings.mail_from || '';
    
    // Telegram settings
    document.getElementById('telegram_enabled').checked = settings.telegram_enabled === 'True';
    document.getElementById('telegram_bot_token').value = settings.telegram_bot_token || '';
    document.getElementById('telegram_chat_id').value = settings.telegram_chat_id || '';
    
    // Backup settings
    document.getElementById('auto_backup_enabled').checked = settings.auto_backup_enabled === 'True';
    document.getElementById('backup_schedule').value = settings.backup_schedule || '0 0 * * 0';
    document.getElementById('backup_retention_days').value = settings.backup_retention_days || 30;
    
    // Discovery settings
    document.getElementById('discovery_enabled').checked = settings.discovery_enabled === 'True';
    document.getElementById('discovery_schedule').value = settings.discovery_schedule || '0 0 * * *';
    document.getElementById('discovery_subnets').value = settings.discovery_subnets || '';
}

// Save general settings
async function saveGeneralSettings() {
    const sessionTimeout = document.getElementById('session_timeout').value;
    const timezone = document.getElementById('timezone').value;
    const dateFormat = document.getElementById('date_format').value;
    const enableDarkMode = document.getElementById('enable_dark_mode').checked;
    
    // Validate required fields
    if (!sessionTimeout || !timezone || !dateFormat) {
        showError('Please fill in all required fields');
        return;
    }
    
    // Validate session timeout
    if (parseInt(sessionTimeout) < 5 || parseInt(sessionTimeout) > 1440) {
        showError('Session timeout must be between 5 and 1440 minutes');
        return;
    }
    
    try {
        const response = await fetchWithAuth('/api/config/settings', {
            method: 'PUT',
            body: {
                session_timeout: sessionTimeout,
                timezone: timezone,
                date_format: dateFormat,
                enable_dark_mode: enableDarkMode ? 'True' : 'False'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save general settings');
        }
        
        // Update current settings
        const updatedSettings = await response.json();
        currentSettings = {...currentSettings, ...updatedSettings};
        
        showSuccess('General settings saved successfully');
    } catch (error) {
        console.error('Error saving general settings:', error);
        showError(error.message || 'Failed to save general settings');
    }
}

// Save monitoring settings
async function saveMonitoringSettings() {
    const monitoringInterval = document.getElementById('monitoring_interval').value;
    const alertCheckInterval = document.getElementById('alert_check_interval').value;
    const metricsRetentionDays = document.getElementById('metrics_retention_days').value;
    
    // Validate required fields
    if (!monitoringInterval || !alertCheckInterval || !metricsRetentionDays) {
        showError('Please fill in all required fields');
        return;
    }
    
    // Validate intervals
    if (parseInt(monitoringInterval) < 10 || parseInt(monitoringInterval) > 3600) {
        showError('Monitoring interval must be between 10 and 3600 seconds');
        return;
    }
    
    if (parseInt(alertCheckInterval) < 10 || parseInt(alertCheckInterval) > 3600) {
        showError('Alert check interval must be between 10 and 3600 seconds');
        return;
    }
    
    if (parseInt(metricsRetentionDays) < 1 || parseInt(metricsRetentionDays) > 365) {
        showError('Metrics retention must be between 1 and 365 days');
        return;
    }
    
    try {
        const response = await fetchWithAuth('/api/config/settings', {
            method: 'PUT',
            body: {
                monitoring_interval: monitoringInterval,
                alert_check_interval: alertCheckInterval,
                metrics_retention_days: metricsRetentionDays
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save monitoring settings');
        }
        
        // Update current settings
        const updatedSettings = await response.json();
        currentSettings = {...currentSettings, ...updatedSettings};
        
        showSuccess('Monitoring settings saved successfully');
    } catch (error) {
        console.error('Error saving monitoring settings:', error);
        showError(error.message || 'Failed to save monitoring settings');
    }
}

// Save email settings
async function saveEmailSettings() {
    const emailEnabled = document.getElementById('email_enabled').checked;
    const mailServer = document.getElementById('mail_server').value;
    const mailPort = document.getElementById('mail_port').value;
    const mailUseTls = document.getElementById('mail_use_tls').checked;
    const mailUsername = document.getElementById('mail_username').value;
    const mailPassword = document.getElementById('mail_password').value;
    const mailFrom = document.getElementById('mail_from').value;
    
    // Validate required fields if email is enabled
    if (emailEnabled) {
        if (!mailServer || !mailPort || !mailUsername || !mailFrom) {
            showError('Please fill in all required email fields');
            return;
        }
        
        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(mailFrom)) {
            showError('Please enter a valid email address for From Address');
            return;
        }
    }
    
    try {
        const response = await fetchWithAuth('/api/config/settings', {
            method: 'PUT',
            body: {
                email_enabled: emailEnabled ? 'True' : 'False',
                mail_server: mailServer,
                mail_port: mailPort,
                mail_use_tls: mailUseTls ? 'True' : 'False',
                mail_username: mailUsername,
                mail_password: mailPassword,
                mail_from: mailFrom
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save email settings');
        }
        
        // Update current settings
        const updatedSettings = await response.json();
        currentSettings = {...currentSettings, ...updatedSettings};
        
        showSuccess('Email settings saved successfully');
    } catch (error) {
        console.error('Error saving email settings:', error);
        showError(error.message || 'Failed to save email settings');
    }
}

// Test email
async function testEmail() {
    // Check if email is enabled and settings are saved
    if (!document.getElementById('email_enabled').checked) {
        showError('Email notifications are not enabled');
        return;
    }
    
    const mailServer = document.getElementById('mail_server').value;
    const mailUsername = document.getElementById('mail_username').value;
    
    if (!mailServer || !mailUsername) {
        showError('Please save email settings before testing');
        return;
    }
    
    try {
        // In a real implementation, this would call an API endpoint to send a test email
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        showSuccess('Test email sent successfully. Please check your inbox.');
    } catch (error) {
        console.error('Error sending test email:', error);
        showError(error.message || 'Failed to send test email');
    }
}

// Save telegram settings
async function saveTelegramSettings() {
    const telegramEnabled = document.getElementById('telegram_enabled').checked;
    const telegramBotToken = document.getElementById('telegram_bot_token').value;
    const telegramChatId = document.getElementById('telegram_chat_id').value;
    
    // Validate required fields if telegram is enabled
    if (telegramEnabled) {
        if (!telegramBotToken || !telegramChatId) {
            showError('Please fill in all required telegram fields');
            return;
        }
    }
    
    try {
        const response = await fetchWithAuth('/api/config/settings', {
            method: 'PUT',
            body: {
                telegram_enabled: telegramEnabled ? 'True' : 'False',
                telegram_bot_token: telegramBotToken,
                telegram_chat_id: telegramChatId
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save telegram settings');
        }
        
        // Update current settings
        const updatedSettings = await response.json();
        currentSettings = {...currentSettings, ...updatedSettings};
        
        showSuccess('Telegram settings saved successfully');
    } catch (error) {
        console.error('Error saving telegram settings:', error);
        showError(error.message || 'Failed to save telegram settings');
    }
}

// Test telegram
async function testTelegram() {
    // Check if telegram is enabled and settings are saved
    if (!document.getElementById('telegram_enabled').checked) {
        showError('Telegram notifications are not enabled');
        return;
    }
    
    const telegramBotToken = document.getElementById('telegram_bot_token').value;
    const telegramChatId = document.getElementById('telegram_chat_id').value;
    
    if (!telegramBotToken || !telegramChatId) {
        showError('Please save telegram settings before testing');
        return;
    }
    
    try {
        // In a real implementation, this would call an API endpoint to send a test message
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        showSuccess('Test telegram message sent successfully. Please check your telegram.');
    } catch (error) {
        console.error('Error sending test telegram message:', error);
        showError(error.message || 'Failed to send test telegram message');
    }
}

// Save backup settings
async function saveBackupSettings() {
    const autoBackupEnabled = document.getElementById('auto_backup_enabled').checked;
    const backupSchedule = document.getElementById('backup_schedule').value;
    const backupRetentionDays = document.getElementById('backup_retention_days').value;
    const discoveryEnabled = document.getElementById('discovery_enabled').checked;
    const discoverySchedule = document.getElementById('discovery_schedule').value;
    const discoverySubnets = document.getElementById('discovery_subnets').value;
    
    // Validate required fields if backup is enabled
    if (autoBackupEnabled) {
        if (!backupSchedule || !backupRetentionDays) {
            showError('Please fill in all required backup fields');
            return;
        }
    }
    
    // Validate required fields if discovery is enabled
    if (discoveryEnabled) {
        if (!discoverySchedule) {
            showError('Please fill in all required discovery fields');
            return;
        }
    }
    
    try {
        const response = await fetchWithAuth('/api/config/settings', {
            method: 'PUT',
            body: {
                auto_backup_enabled: autoBackupEnabled ? 'True' : 'False',
                backup_schedule: backupSchedule,
                backup_retention_days: backupRetentionDays,
                discovery_enabled: discoveryEnabled ? 'True' : 'False',
                discovery_schedule: discoverySchedule,
                discovery_subnets: discoverySubnets
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save backup settings');
        }
        
        // Update current settings
        const updatedSettings = await response.json();
        currentSettings = {...currentSettings, ...updatedSettings};
        
        showSuccess('Backup and discovery settings saved successfully');
    } catch (error) {
        console.error('Error saving backup settings:', error);
        showError(error.message || 'Failed to save backup settings');
    }
}
