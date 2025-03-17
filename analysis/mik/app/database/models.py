from app import db
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), default='user')  # 'admin', 'user', 'operator'
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Device(db.Model):
    """MikroTik device model"""
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    api_port = Column(Integer, default=8728)  # Default MikroTik API port
    use_ssl = Column(Boolean, default=False)  # Whether to use SSL
    model = Column(String(100))
    location = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    metrics = relationship("Metric", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'username': self.username,
            'password': '********',  # Mask password for security
            'api_port': self.api_port,
            'use_ssl': self.use_ssl,
            'model': self.model,
            'location': self.location,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Metric(db.Model):
    """Time series metrics for devices"""
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    metric_type = Column(String(50), nullable=False)  # 'cpu', 'memory', 'disk', 'interface'
    metric_name = Column(String(50), nullable=False)  # 'load', 'usage', 'traffic_in', 'traffic_out'
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    device = relationship("Device", back_populates="metrics")
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'metric_type': self.metric_type,
            'metric_name': self.metric_name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class AlertRule(db.Model):
    """Rules for triggering alerts"""
    __tablename__ = 'alert_rules'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    metric = Column(String(50), nullable=False)  # 'cpu_load', 'memory_usage', 'disk_usage', etc.
    condition = Column(String(10), nullable=False)  # '>', '<', '>=', '<=', '=='
    threshold = Column(Float, nullable=False)
    duration = Column(Integer, default=0)  # Duration in seconds to check average
    enabled = Column(Boolean, default=True)
    notify_email = Column(Boolean, default=False)
    notify_telegram = Column(Boolean, default=False)
    email_recipients = Column(String(255))
    message_template = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    device = relationship("Device")
    alerts = relationship("Alert", back_populates="rule", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'device_id': self.device_id,
            'device_name': self.device.name if self.device else None,
            'metric': self.metric,
            'condition': self.condition,
            'threshold': self.threshold,
            'duration': self.duration,
            'enabled': self.enabled,
            'notify_email': self.notify_email,
            'notify_telegram': self.notify_telegram,
            'email_recipients': self.email_recipients,
            'message_template': self.message_template,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Alert(db.Model):
    """Triggered alerts history"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey('alert_rules.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    metric = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    condition = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey('users.id'))
    acknowledged_at = Column(DateTime)
    
    # Relationships
    rule = relationship("AlertRule", back_populates="alerts")
    device = relationship("Device", back_populates="alerts")
    user = relationship("User")
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule.name if self.rule else None,
            'device_id': self.device_id,
            'device_name': self.device.name if self.device else None,
            'metric': self.metric,
            'value': self.value,
            'threshold': self.threshold,
            'condition': self.condition,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }

class Setting(db.Model):
    """Application settings"""
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value
        }
