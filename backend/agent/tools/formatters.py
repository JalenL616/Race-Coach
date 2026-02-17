from ..models import SplitEntry, SplitsResponse

def format_pace(pace_minutes: float) -> str:
    minutes = int(pace_minutes)
    seconds = int((pace_minutes - minutes) * 60)
    return f"{minutes}:{seconds:02d}"

def format_time(total_minutes: float) -> str:
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    seconds = int((total_minutes % 1) * 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"

def format_mile_splits(splits: list[tuple[float, float]]) -> list[SplitEntry]:
    split_entry_list = []
    cumulative_time = 0
    for mile_num, (distance, pace) in enumerate(splits, start=1):
        segment_time = distance * pace
        cumulative_time += segment_time

        if distance < 1.0:
              mile_label = f"Finish ({distance:.1f}mi)"
        else:
            mile_label = mile_num

        new_entry = SplitEntry(mile=mile_label, 
                               distance=distance,
                               pace_minutes=pace, 
                               pace_formatted=format_pace(pace), 
                               cumulative_time=cumulative_time,
                               cumulative_formatted=format_time(cumulative_time))
        split_entry_list.append(new_entry)
    return split_entry_list