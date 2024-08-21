# Streamlit Supabase Storage browser

A streamlit component serve as Supabase Storage browser.

## Install (Not ready yet)

```
pip install streamlit-supabase-storage-browser
```
## Usage Example

```python
import os
import streamlit as st
from streamlit_supabase_storage_browser import st_supabase_storage_browser
from supabase import create_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
bucket_id = os.getenv('SUPABASE_BUCKET_ID')

st.header('Default Options')
event = st_supabase_storage_browser(supabase, bucket_id, key='A')
st.write(event)
```

## API

| name                     | usage                                                                     | type           | required                                                | default |
|--------------------------|---------------------------------------------------------------------------|----------------|---------------------------------------------------------|---------|
| key                      | react key                                                                 | string         | No. But I suggest giving each component a different key | None    |
| supabase                 | Supabase client                                                           | SyncClient     | Yes                                                     |         |
| path                     | the path of dir                                                           | string         | No. If not set, root is used.                           |         |
| show_preview             | if preview the file be clicked                                            | bool           | No                                                      | True    |
| show_preview_top         | Whether to render the preview above the file browser                      | bool           | No                                                      | False   |
| glob_patterns            | To control file shows, the usage is the same as the patterns of glob.glob | string (regex) | No                                                      | '**/*'  |
| ignore_file_select_event | If ignore the 'file_selected' event                                       | bool           | No                                                      | False   |
| extentions               | Only show the files included in the extentions                            | list           | No                                                      | None    |
| show_delete_file         | If show the button of delete file                                         | bool           | No                                                      | False   |
| show_choose_file         | If show the button of choose file                                         | bool           | No                                                      | False   |
| show_download_file       | If show the button of download file                                       | bool           | No                                                      | True    |
| show_new_folder          | If show the button of new folder                                          | bool           | No                                                      | False   |
| show_upload_file         | If show the button of upload file                                         | bool           | No                                                      | False   |
| limit                    | File number limit                                                         | int            | No                                                      | 10000   |
| use_cache                | If cache file tree                                                        | bool           | No                                                      | False   |

<br/>
