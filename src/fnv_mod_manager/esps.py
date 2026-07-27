import os
import time

# this is done as FNV loads plugins based on last modified time
def set_utimes_in_order(ordered_plugin_paths):
    base = time.time()
    set_utimes_in_order_with_set_base(base, ordered_plugin_paths)

def set_utimes_in_order_with_set_base(base, ordered_plugin_paths):
    for index, plugin_path in enumerate(ordered_plugin_paths):
        mtime = base + index * 60
        os.utime(plugin_path, times=(mtime, mtime))
