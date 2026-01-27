from scipy.interpolate import interp1d
import pandas as pd

# Convert MM:SS or M:SS:SS format to seconds
def time_to_seconds(time_str):
    parts = time_str.split(':')
    if len(parts) == 2:  # MM:SS
        return int(parts[0]) * 60 + float(parts[1])
    else:  # H:MM:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])

# Raw data from the table (as strings)
vdot_raw = [30, 32, 34, 36, 38, 40, 42, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60,
            61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85]

times_5000 = ['30:40', '29:05', '27:39', '26:22', '25:12', '24:08', '23:09', '22:15', '21:50', '21:25', '21:02', '20:39', '20:18', '19:57', '19:36', '19:17', '18:58', '18:40', '18:22', '18:05', '17:49', '17:33', '17:17', '17:03',
             '16:48', '16:34', '16:20', '16:07', '15:53', '15:42', '15:29', '15:18', '15:06', '14:55', '14:48', '14:33', '14:23', '14:13', '14:03', '13:54', '13:44', '13:35', '13:26', '13:17.8', '13:09.3', '13:01.1', '12:53.0', '12:45.2', '12:37.4']

times_half_mara = ['2:21:04', '2:13:49', '2:07:16', '2:01:19', '1:55:55', '1:50:59', '1:46:27', '1:42:17', '1:40:20', '1:38:27', '1:36:38', '1:34:53', '1:33:12', '1:31:35', '1:30:02', '1:28:31', '1:27:04', '1:25:40', '1:24:18', '1:23:00', '1:21:43', '1:20:30', '1:19:18', '1:18:09',
                    '1:17:02', '1:15:57', '1:14:54', '1:13:53', '1:12:53', '1:11:56', '1:11:00', '1:10:05', '1:09:12', '1:08:21', '1:07:31', '1:06:42', '1:05:54', '1:05:08', '1:04:23', '1:03:39', '1:02:56', '1:02:15', '1:01:34', '1:00:54', '1:00:15', '59:38', '59:01', '58:25', '57:50']

times_marathon = ['4:49:17', '4:34:59', '4:22:03', '4:10:19', '3:59:35', '3:49:45', '3:40:43', '3:32:23', '3:28:26', '3:24:39', '3:21:00', '3:17:29', '3:14:06', '3:10:49', '3:07:39', '3:04:36', '3:01:39', '2:58:47', '2:56:01', '2:53:30', '2:50:45', '2:48:14', '2:45:47', '2:43:25',
                   '2:41:08', '2:38:54', '2:36:44', '2:34:38', '2:32:35', '2:30:36', '2:28:40', '2:26:47', '2:24:57', '2:23:10', '2:21:26', '2:19:44', '2:18:05', '2:16:29', '2:14:55', '2:13:23', '2:11:54', '2:10:27', '2:09:02', '2:07:38', '2:06:17', '2:04:57', '2:03:40', '2:02:24', '2:01:10']

# Convert all times to seconds
vdot_data = {
    'VDOT': vdot_raw,
    '5000': [time_to_seconds(t) for t in times_5000],
    '1/2 Marathon': [time_to_seconds(t) for t in times_half_mara],
    'Marathon': [time_to_seconds(t) for t in times_marathon]
}

# Create DataFrame
df = pd.DataFrame(vdot_data)

# Create interpolation functions for each metric
interpolators = {}
for metric in ['5000', '1/2 Marathon', 'Marathon']:
    interpolators[metric] = interp1d(df['VDOT'], df[metric], kind='linear', fill_value='extrapolate')

def get_times(vdot):
    """Get race times for a given VDOT value. Returns times in seconds."""
    if vdot < df['VDOT'].min() or vdot > df['VDOT'].max():
        print(f"Warning: VDOT {vdot} is outside the range {df['VDOT'].min()}-{df['VDOT'].max()}. Extrapolating.")
    
    results = {'VDOT': vdot}
    for metric in ['5000', '1/2 Marathon', 'Marathon']:
        time_seconds = float(interpolators[metric](vdot))
        results[metric] = time_seconds
    
    return results

def seconds_to_time(seconds):
    total_secs = int(round(seconds))
    hours = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    secs = total_secs % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"