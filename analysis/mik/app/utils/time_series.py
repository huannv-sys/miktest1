import logging
import json
from datetime import datetime, timedelta
from app.database.crud import get_metrics_for_device

# Configure logger
logger = logging.getLogger(__name__)

def get_time_series_data(device_id, metric, start_time, end_time):
    """Get time series data for a device metric"""
    try:
        # Parse metric into type and name
        metric_type = None
        metric_name = None
        
        if metric == 'cpu_load':
            metric_type = 'cpu'
            metric_name = 'load'
        elif metric == 'memory_usage':
            metric_type = 'memory'
            metric_name = 'usage'
        elif metric == 'disk_usage':
            metric_type = 'disk'
            metric_name = 'usage'
        # Add more mappings as needed
        
        if not metric_type or not metric_name:
            logger.error(f"Invalid metric: {metric}")
            return {"error": "Invalid metric"}
        
        # Get metrics from database
        metrics = get_metrics_for_device(
            device_id=device_id,
            metric_type=metric_type,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            limit=1000  # Set a reasonable limit
        )
        
        # Format data for charts
        data = {
            "metric": metric,
            "device_id": device_id,
            "data_points": len(metrics),
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "values": []
        }
        
        for m in sorted(metrics, key=lambda x: x.timestamp):
            data["values"].append({
                "timestamp": m.timestamp.isoformat(),
                "value": m.value
            })
        
        return data
    except Exception as e:
        logger.error(f"Error getting time series data: {str(e)}")
        return {"error": str(e)}

def calculate_statistics(data_points):
    """Calculate statistics for a set of data points"""
    if not data_points:
        return {
            "min": 0,
            "max": 0,
            "avg": 0,
            "count": 0,
            "first": 0,
            "last": 0
        }
    
    values = [p["value"] for p in data_points]
    
    return {
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
        "count": len(values),
        "first": data_points[0]["value"],
        "last": data_points[-1]["value"]
    }

def resample_time_series(data_points, interval_minutes=5):
    """Resample time series data to a specified interval"""
    if not data_points:
        return []
    
    # Sort by timestamp
    sorted_points = sorted(data_points, key=lambda x: x["timestamp"])
    
    # Get time range
    start_time = datetime.fromisoformat(sorted_points[0]["timestamp"])
    end_time = datetime.fromisoformat(sorted_points[-1]["timestamp"])
    
    # Generate time intervals
    intervals = []
    current_time = start_time
    
    while current_time <= end_time:
        intervals.append(current_time)
        current_time += timedelta(minutes=interval_minutes)
    
    # Assign data points to intervals
    result = []
    
    for i in range(len(intervals) - 1):
        interval_start = intervals[i]
        interval_end = intervals[i + 1]
        
        # Find points in this interval
        interval_points = []
        
        for point in sorted_points:
            point_time = datetime.fromisoformat(point["timestamp"])
            if interval_start <= point_time < interval_end:
                interval_points.append(point)
        
        # Calculate average for interval
        if interval_points:
            avg_value = sum(p["value"] for p in interval_points) / len(interval_points)
            
            result.append({
                "timestamp": interval_start.isoformat(),
                "value": avg_value
            })
    
    return result
