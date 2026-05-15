# notification — Public & Internal API List

All symbols marked with the `EXPORT_API` macro (`__attribute__((visibility("default")))`).

- **Total export sites**: 522
- **Files**: 52
- **Classes** (`class EXPORT_API`): 43
- **C functions** (`extern "C" EXPORT_API`): 183
- **Free functions** (`EXPORT_API` on `.c`/`.cc`): 296
- **Methods/ctors** (`EXPORT_API ClassName::...`): 0

## File summary

| File | Count | Visibility |
|------|------:|-----------|
| `src/notification-ex/abstract_action.h` | 1 | Public |
| `src/notification-ex/abstract_item.h` | 7 | Public |
| `src/notification-ex/action_inflator.h` | 1 | Public |
| `src/notification-ex/app_control_action.h` | 1 | Public |
| `src/notification-ex/button_item.h` | 1 | Public |
| `src/notification-ex/chat_message_item.h` | 1 | Public |
| `src/notification-ex/checkbox_item.h` | 1 | Public |
| `src/notification-ex/db_manager.h` | 1 | Public |
| `src/notification-ex/dbus_connection_manager.h` | 1 | Public |
| `src/notification-ex/dbus_event_listener.h` | 1 | Public |
| `src/notification-ex/dbus_sender.h` | 1 | Public |
| `src/notification-ex/default_action_factory.h` | 1 | Public |
| `src/notification-ex/default_item_factory.h` | 1 | Public |
| `src/notification-ex/entry_item.h` | 1 | Public |
| `src/notification-ex/event_info_internal.h` | 1 | Internal |
| `src/notification-ex/event_listener_interface.h` | 1 | Public |
| `src/notification-ex/event_observer_interface.h` | 1 | Public |
| `src/notification-ex/event_sender_interface.h` | 1 | Public |
| `src/notification-ex/group_item.h` | 1 | Public |
| `src/notification-ex/iaction_factory.h` | 1 | Public |
| `src/notification-ex/icon_item.h` | 1 | Public |
| `src/notification-ex/ievent_info.h` | 1 | Public |
| `src/notification-ex/iitem_factory.h` | 1 | Public |
| `src/notification-ex/iitem_info.h` | 1 | Public |
| `src/notification-ex/iitem_info_internal.h` | 1 | Internal |
| `src/notification-ex/image_item.h` | 1 | Public |
| `src/notification-ex/input_selector_item.h` | 1 | Public |
| `src/notification-ex/item_inflator.h` | 1 | Public |
| `src/notification-ex/manager.h` | 1 | Public |
| `src/notification-ex/mock_listener.h` | 1 | Public |
| `src/notification-ex/mock_sender.h` | 1 | Public |
| `src/notification-ex/progress_item.h` | 1 | Public |
| `src/notification-ex/reporter.h` | 1 | Public |
| `src/notification-ex/shared_file.h` | 1 | Public |
| `src/notification-ex/stub.cc` | 183 | Public (C ABI) |
| `src/notification-ex/text_item.h` | 1 | Public |
| `src/notification-ex/time_item.h` | 1 | Public |
| `src/notification-ex/visibility_action.h` | 1 | Public |
| `src/notification/src/notification.c` | 57 | Public |
| `src/notification/src/notification_db.c` | 7 | Public |
| `src/notification/src/notification_error.c` | 1 | Public |
| `src/notification/src/notification_internal.c` | 105 | Internal |
| `src/notification/src/notification_internal_tidl.c` | 8 | Internal |
| `src/notification/src/notification_ipc.c` | 2 | Public |
| `src/notification/src/notification_list.c` | 15 | Public |
| `src/notification/src/notification_noti.c` | 24 | Public |
| `src/notification/src/notification_ongoing.c` | 2 | Public |
| `src/notification/src/notification_setting.c` | 50 | Public |
| `src/notification/src/notification_setting_service.c` | 13 | Public |
| `src/notification/src/notification_shared_file.c` | 6 | Public |
| `src/notification/src/notification_status.c` | 3 | Public |
| `src/notification/src/notification_viewer.c` | 3 | Public |

## Details

### `src/notification-ex/abstract_action.h` — Public — 1 APIs

**Classes**

- L41: `class EXPORT_API AbstractAction {`


### `src/notification-ex/abstract_item.h` — Public — 7 APIs

**Classes**

- L46: `class EXPORT_API ReceiverGroup {`
- L60: `class EXPORT_API Color {`
- L189: `class EXPORT_API Padding {`
- L318: `class EXPORT_API Geometry {`
- L446: `class EXPORT_API Style {`
- L644: `class EXPORT_API LEDInfo {`
- L715: `class EXPORT_API AbstractItem {`


### `src/notification-ex/action_inflator.h` — Public — 1 APIs

**Classes**

- L33: `class EXPORT_API ActionInflator {`


### `src/notification-ex/app_control_action.h` — Public — 1 APIs

**Classes**

- L34: `class EXPORT_API AppControlAction : public AbstractAction {`


### `src/notification-ex/button_item.h` — Public — 1 APIs

**Classes**

- L34: `class EXPORT_API ButtonItem : public AbstractItem {`


### `src/notification-ex/chat_message_item.h` — Public — 1 APIs

**Classes**

- L39: `class EXPORT_API ChatMessageItem : public AbstractItem {`


### `src/notification-ex/checkbox_item.h` — Public — 1 APIs

**Classes**

- L34: `class EXPORT_API CheckBoxItem : public AbstractItem {`


### `src/notification-ex/db_manager.h` — Public — 1 APIs

**Classes**

- L36: `class EXPORT_API DBManager {`


### `src/notification-ex/dbus_connection_manager.h` — Public — 1 APIs

**Classes**

- L31: `class EXPORT_API DBusConnectionManager {`


### `src/notification-ex/dbus_event_listener.h` — Public — 1 APIs

**Classes**

- L27: `class EXPORT_API DBusEventListener : public IEventListener {`


### `src/notification-ex/dbus_sender.h` — Public — 1 APIs

**Classes**

- L34: `class EXPORT_API DBusSender : public IEventSender {`


### `src/notification-ex/default_action_factory.h` — Public — 1 APIs

**Classes**

- L32: `class EXPORT_API DefaultActionFactory : public IActionFactory {`


### `src/notification-ex/default_item_factory.h` — Public — 1 APIs

**Classes**

- L32: `class EXPORT_API DefaultItemFactory : public IItemFactory {`


### `src/notification-ex/entry_item.h` — Public — 1 APIs

**Classes**

- L37: `class EXPORT_API EntryItem : public AbstractItem {`


### `src/notification-ex/event_info_internal.h` — Internal — 1 APIs

**Classes**

- L34: `class EXPORT_API EventInfo : public IEventInfoInternal {`


### `src/notification-ex/event_listener_interface.h` — Public — 1 APIs

**Classes**

- L32: `class EXPORT_API IEventListener {`


### `src/notification-ex/event_observer_interface.h` — Public — 1 APIs

**Classes**

- L33: `class EXPORT_API IEventObserver {`


### `src/notification-ex/event_sender_interface.h` — Public — 1 APIs

**Classes**

- L34: `class EXPORT_API IEventSender {`


### `src/notification-ex/group_item.h` — Public — 1 APIs

**Classes**

- L35: `class EXPORT_API GroupItem : public AbstractItem {`


### `src/notification-ex/iaction_factory.h` — Public — 1 APIs

**Classes**

- L33: `class EXPORT_API IActionFactory {`


### `src/notification-ex/icon_item.h` — Public — 1 APIs

**Classes**

- L34: `class EXPORT_API IconItem : public ImageItem {`


### `src/notification-ex/ievent_info.h` — Public — 1 APIs

**Classes**

- L31: `class EXPORT_API IEventInfo {`


### `src/notification-ex/iitem_factory.h` — Public — 1 APIs

**Classes**

- L33: `class EXPORT_API IItemFactory {`


### `src/notification-ex/iitem_info.h` — Public — 1 APIs

**Classes**

- L30: `class EXPORT_API IItemInfo {`


### `src/notification-ex/iitem_info_internal.h` — Internal — 1 APIs

**Classes**

- L33: `class EXPORT_API IItemInfoInternal : public IItemInfo {`


### `src/notification-ex/image_item.h` — Public — 1 APIs

**Classes**

- L35: `class EXPORT_API ImageItem : public AbstractItem {`


### `src/notification-ex/input_selector_item.h` — Public — 1 APIs

**Classes**

- L34: `class EXPORT_API InputSelectorItem : public AbstractItem {`


### `src/notification-ex/item_inflator.h` — Public — 1 APIs

**Classes**

- L33: `class EXPORT_API ItemInflator {`


### `src/notification-ex/manager.h` — Public — 1 APIs

**Classes**

- L37: `class EXPORT_API Manager : public IEventObserver {`


### `src/notification-ex/mock_listener.h` — Public — 1 APIs

**Classes**

- L28: `class EXPORT_API MockEventsListener : public IEventListener {`


### `src/notification-ex/mock_sender.h` — Public — 1 APIs

**Classes**

- L28: `class EXPORT_API MockSender : public IEventSender {`


### `src/notification-ex/progress_item.h` — Public — 1 APIs

**Classes**

- L34: `class EXPORT_API ProgressItem : public AbstractItem {`


### `src/notification-ex/reporter.h` — Public — 1 APIs

**Classes**

- L38: `class EXPORT_API Reporter : public IEventObserver {`


### `src/notification-ex/shared_file.h` — Public — 1 APIs

**Classes**

- L38: `class EXPORT_API SharedFile {`


### `src/notification-ex/stub.cc` — Public (C ABI) — 183 APIs

**C functions (extern "C")**

- L292: `extern "C" EXPORT_API int noti_ex_action_app_control_create( noti_ex_action_h *handle, app_control_h app_control, const char *extra) {`
- L323: `extern "C" EXPORT_API int noti_ex_action_app_control_set( noti_ex_action_h handle, app_control_h app_control) {`
- L341: `extern "C" EXPORT_API int noti_ex_action_app_control_get( noti_ex_action_h handle, app_control_h *app_control) {`
- L367: `extern "C" EXPORT_API int noti_ex_item_button_create(noti_ex_item_h *handle, const char *id, const char *title) {`
- L392: `extern "C" EXPORT_API int noti_ex_item_button_get_title(noti_ex_item_h handle, char **title) {`
- L425: `extern "C" EXPORT_API int noti_ex_item_button_set_multi_language_title( noti_ex_item_h handle, noti_ex_multi_lang_h multi) {`
- L456: `extern "C" EXPORT_API int noti_ex_item_button_set_image( noti_ex_item_h handle, const char *path) {`
- L478: `extern "C" EXPORT_API int noti_ex_item_button_get_image( noti_ex_item_h handle, char **path) {`
- L503: `extern "C" EXPORT_API int noti_ex_item_button_set_contents( noti_ex_item_h handle, const char *contents) {`
- L525: `extern "C" EXPORT_API int noti_ex_item_button_get_contents( noti_ex_item_h handle, char **contents) {`
- L550: `extern "C" EXPORT_API int noti_ex_item_chat_message_create( noti_ex_item_h *handle, const char *id, noti_ex_item_h name, noti_ex_item_h text, noti_ex_item_h image, noti_ex_item_h time, noti_ex_item_ch...`
- L585: `extern "C" EXPORT_API int noti_ex_item_chat_message_get_name( noti_ex_item_h handle, noti_ex_item_h *name) {`
- L608: `extern "C" EXPORT_API int noti_ex_item_chat_message_get_text( noti_ex_item_h handle, noti_ex_item_h *text) {`
- L632: `extern "C" EXPORT_API int noti_ex_item_chat_message_get_image( noti_ex_item_h handle, noti_ex_item_h *image) {`
- L656: `extern "C" EXPORT_API int noti_ex_item_chat_message_get_time( noti_ex_item_h handle, noti_ex_item_h *time) {`
- L680: `extern "C" EXPORT_API int noti_ex_item_chat_message_get_message_type( noti_ex_item_h handle, noti_ex_item_chat_message_type_e *message_type) {`
- L701: `extern "C" EXPORT_API int noti_ex_item_checkbox_create(noti_ex_item_h *handle, const char *id, const char *title, bool checked) {`
- L727: `extern "C" EXPORT_API int noti_ex_item_checkbox_get_title(noti_ex_item_h handle, char **title) {`
- L759: `extern "C" EXPORT_API int noti_ex_item_checkbox_set_multi_language_title( noti_ex_item_h handle, noti_ex_multi_lang_h multi) {`
- L789: `extern "C" EXPORT_API int noti_ex_item_checkbox_get_check_state( noti_ex_item_h handle, bool *checked) {`
- L809: `extern "C" EXPORT_API int noti_ex_item_checkbox_set_check_state( noti_ex_item_h handle, bool checked) {`
- L831: `extern "C" EXPORT_API int noti_ex_item_entry_create(noti_ex_item_h *handle, const char *id) {`
- L858: `extern "C" EXPORT_API int noti_ex_item_entry_get_text(noti_ex_item_h handle, char **text) {`
- L891: `extern "C" EXPORT_API int noti_ex_item_entry_set_text(noti_ex_item_h handle, const char *text) {`
- L911: `extern "C" EXPORT_API int noti_ex_item_entry_set_multi_language( noti_ex_item_h handle, noti_ex_multi_lang_h multi) {`
- L941: `extern "C" EXPORT_API int noti_ex_event_info_clone(noti_ex_event_info_h handle, noti_ex_event_info_h* cloned_handle) {`
- L957: `extern "C" EXPORT_API int noti_ex_event_info_destroy( noti_ex_event_info_h handle) {`
- L971: `extern "C" EXPORT_API int noti_ex_event_info_get_event_type( noti_ex_event_info_h handle, noti_ex_event_info_type_e *event_type) {`
- L986: `extern "C" EXPORT_API int noti_ex_event_info_get_owner( noti_ex_event_info_h handle, char **owner) {`
- L1000: `extern "C" EXPORT_API int noti_ex_event_info_get_channel( noti_ex_event_info_h handle, char **channel) {`
- L1014: `extern "C" EXPORT_API int noti_ex_event_info_get_item_id( noti_ex_event_info_h handle, char **item_id) {`
- L1028: `extern "C" EXPORT_API int noti_ex_event_info_get_request_id( noti_ex_event_info_h handle, int *req_id) {`
- L1042: `extern "C" EXPORT_API int noti_ex_item_group_create(noti_ex_item_h *handle, const char *id) {`
- L1069: `extern "C" EXPORT_API int noti_ex_item_group_set_direction(noti_ex_item_h handle, bool vertical) {`
- L1089: `extern "C" EXPORT_API int noti_ex_item_group_is_vertical(noti_ex_item_h handle, bool *vertical) {`
- L1109: `extern "C" EXPORT_API int noti_ex_item_group_get_app_label(noti_ex_item_h handle, char **label) {`
- L1135: `extern "C" EXPORT_API int noti_ex_item_group_add_child(noti_ex_item_h handle, noti_ex_item_h child) {`
- L1155: `extern "C" EXPORT_API int noti_ex_item_group_remove_child(noti_ex_item_h handle, const char *item_id) {`
- L1175: `extern "C" EXPORT_API int noti_ex_item_group_foreach_child(noti_ex_item_h handle, noti_ex_item_group_foreach_child_cb callback, void *data) {`
- L1206: `extern "C" EXPORT_API int noti_ex_item_image_create(noti_ex_item_h *handle, const char *id, const char *image_path) {`
- L1233: `extern "C" EXPORT_API int noti_ex_item_image_get_image_path( noti_ex_item_h handle, char **image_path) {`
- L1261: `extern "C" EXPORT_API int noti_ex_item_input_selector_create( noti_ex_item_h *handle, const char *id) {`
- L1288: `extern "C" EXPORT_API int noti_ex_item_input_selector_get_contents( noti_ex_item_h handle, char ***contents_list, int *count) {`
- L1338: `extern "C" EXPORT_API int noti_ex_item_input_selector_set_contents( noti_ex_item_h handle, const char **contents, int count) {`
- L1363: `extern "C" EXPORT_API int noti_ex_item_input_selector_set_multi_language_contents( noti_ex_item_h handle, noti_ex_multi_lang_h* multi_language_list, int count) {`
- L1394: `extern "C" EXPORT_API int noti_ex_color_create(noti_ex_color_h *handle, unsigned char a, unsigned char r, unsigned char g, unsigned char b) {`
- L1416: `extern "C" EXPORT_API int noti_ex_color_destroy(noti_ex_color_h handle) {`
- L1431: `extern "C" EXPORT_API int noti_ex_color_get_alpha(noti_ex_color_h handle, unsigned char *val) {`
- L1447: `extern "C" EXPORT_API int noti_ex_color_get_red(noti_ex_color_h handle, unsigned char *val) {`
- L1463: `extern "C" EXPORT_API int noti_ex_color_get_green(noti_ex_color_h handle, unsigned char *val) {`
- L1479: `extern "C" EXPORT_API int noti_ex_color_get_blue(noti_ex_color_h handle, unsigned char *val) {`
- L1495: `extern "C" EXPORT_API int noti_ex_padding_create(noti_ex_padding_h *handle, int left, int top, int right, int bottom) {`
- L1519: `extern "C" EXPORT_API int noti_ex_padding_destroy(noti_ex_padding_h handle) {`
- L1534: `extern "C" EXPORT_API int noti_ex_padding_get_left(noti_ex_padding_h handle, int *val) {`
- L1550: `extern "C" EXPORT_API int noti_ex_padding_get_top(noti_ex_padding_h handle, int *val) {`
- L1566: `extern "C" EXPORT_API int noti_ex_padding_get_right(noti_ex_padding_h handle, int *val) {`
- L1582: `extern "C" EXPORT_API int noti_ex_padding_get_bottom(noti_ex_padding_h handle, int *val) {`
- L1598: `extern "C" EXPORT_API int noti_ex_geometry_create(noti_ex_geometry_h *handle, int x, int y, int w, int h) {`
- L1622: `extern "C" EXPORT_API int noti_ex_geometry_destroy(noti_ex_geometry_h handle) {`
- L1637: `extern "C" EXPORT_API int noti_ex_geometry_get_x(noti_ex_geometry_h handle, int *val) {`
- L1653: `extern "C" EXPORT_API int noti_ex_geometry_get_y(noti_ex_geometry_h handle, int *val) {`
- L1669: `extern "C" EXPORT_API int noti_ex_geometry_get_width(noti_ex_geometry_h handle, int *val) {`
- L1685: `extern "C" EXPORT_API int noti_ex_geometry_get_height(noti_ex_geometry_h handle, int *val) {`
- L1701: `extern "C" EXPORT_API int noti_ex_style_create(noti_ex_style_h *handle, noti_ex_color_h color, noti_ex_padding_h padding, noti_ex_geometry_h geometry) {`
- L1734: `extern "C" EXPORT_API int noti_ex_style_destroy(noti_ex_style_h handle) {`
- L1749: `extern "C" EXPORT_API int noti_ex_style_get_padding(noti_ex_style_h handle, noti_ex_padding_h *padding) {`
- L1781: `extern "C" EXPORT_API int noti_ex_style_set_padding(noti_ex_style_h handle, noti_ex_padding_h padding) {`
- L1803: `extern "C" EXPORT_API int noti_ex_style_get_color(noti_ex_style_h handle, noti_ex_color_h *color) {`
- L1832: `extern "C" EXPORT_API int noti_ex_style_set_color( noti_ex_style_h handle, noti_ex_color_h color) {`
- L1854: `extern "C" EXPORT_API int noti_ex_style_get_geometry(noti_ex_style_h handle, noti_ex_geometry_h *geometry) {`
- L1885: `extern "C" EXPORT_API int noti_ex_style_set_geometry( noti_ex_style_h handle, noti_ex_geometry_h geometry) {`
- L1907: `extern "C" EXPORT_API int noti_ex_style_get_background_image( noti_ex_style_h handle, char** background_image) {`
- L1927: `extern "C" EXPORT_API int noti_ex_style_set_background_image( noti_ex_style_h handle, char* background_image) {`
- L1946: `extern "C" EXPORT_API int noti_ex_style_get_background_color( noti_ex_style_h handle, noti_ex_color_h* color) {`
- L1975: `extern "C" EXPORT_API int noti_ex_style_set_background_color( noti_ex_style_h handle, noti_ex_color_h color) {`
- L1997: `extern "C" EXPORT_API int noti_ex_led_info_create(noti_ex_led_info_h *handle, noti_ex_color_h color) {`
- L2020: `extern "C" EXPORT_API int noti_ex_led_info_destroy(noti_ex_led_info_h handle) {`
- L2035: `extern "C" EXPORT_API int noti_ex_led_info_set_on_period( noti_ex_led_info_h handle, int ms) {`
- L2052: `extern "C" EXPORT_API int noti_ex_led_info_get_on_period( noti_ex_led_info_h handle, int *ms) {`
- L2069: `extern "C" EXPORT_API int noti_ex_led_info_set_off_period( noti_ex_led_info_h handle, int ms) {`
- L2086: `extern "C" EXPORT_API int noti_ex_led_info_get_off_period( noti_ex_led_info_h handle, int *ms) {`
- L2103: `extern "C" EXPORT_API int noti_ex_led_info_get_color( noti_ex_led_info_h handle, noti_ex_color_h *color) {`
- L2133: `extern "C" EXPORT_API int noti_ex_led_info_set_color( noti_ex_led_info_h handle, noti_ex_color_h color) {`
- L2155: `extern "C" EXPORT_API int noti_ex_action_destroy(noti_ex_action_h handle) {`
- L2171: `extern "C" EXPORT_API int noti_ex_action_get_type(noti_ex_action_h handle, int *type) {`
- L2188: `extern "C" EXPORT_API int noti_ex_action_is_local(noti_ex_action_h handle, bool *local) {`
- L2205: `extern "C" EXPORT_API int noti_ex_action_execute(noti_ex_action_h handle, noti_ex_item_h item) {`
- L2222: `extern "C" EXPORT_API int noti_ex_action_get_extra(noti_ex_action_h handle, char **extra) {`
- L2247: `extern "C" EXPORT_API int noti_ex_item_info_get_hide_time( noti_ex_item_info_h handle, int *hide_time) {`
- L2261: `extern "C" EXPORT_API int noti_ex_item_info_set_hide_time( noti_ex_item_info_h handle, int hide_time) {`
- L2275: `extern "C" EXPORT_API int noti_ex_item_info_get_delete_time( noti_ex_item_info_h handle, int *delete_time) {`
- L2289: `extern "C" EXPORT_API int noti_ex_item_info_set_delete_time( noti_ex_item_info_h handle, int delete_time) {`
- L2303: `extern "C" EXPORT_API int noti_ex_item_info_get_time( noti_ex_item_info_h handle, time_t *time) {`
- L2318: `extern "C" EXPORT_API int noti_ex_item_destroy(noti_ex_item_h handle) {`
- L2332: `extern "C" EXPORT_API int noti_ex_item_find_by_id(noti_ex_item_h handle, const char *id, noti_ex_item_h *item) {`
- L2354: `extern "C" EXPORT_API int noti_ex_item_get_type(noti_ex_item_h handle, int *type) {`
- L2370: `extern "C" EXPORT_API int noti_ex_item_get_id(noti_ex_item_h handle, char **id) {`
- L2385: `extern "C" EXPORT_API int noti_ex_item_set_id(noti_ex_item_h handle, const char *id) {`
- L2399: `extern "C" EXPORT_API int noti_ex_item_get_action(noti_ex_item_h handle, noti_ex_action_h *action) {`
- L2419: `extern "C" EXPORT_API int noti_ex_item_set_action(noti_ex_item_h handle, noti_ex_action_h action) {`
- L2441: `extern "C" EXPORT_API int noti_ex_item_get_style(noti_ex_item_h handle, noti_ex_style_h *style) {`
- L2471: `extern "C" EXPORT_API int noti_ex_item_set_style(noti_ex_item_h handle, noti_ex_style_h style) {`
- L2492: `extern "C" EXPORT_API int noti_ex_item_set_visible(noti_ex_item_h handle, bool visible) {`
- L2507: `extern "C" EXPORT_API int noti_ex_item_get_visible(noti_ex_item_h handle, bool *visible) {`
- L2522: `extern "C" EXPORT_API int noti_ex_item_set_enable(noti_ex_item_h handle, bool enable) {`
- L2537: `extern "C" EXPORT_API int noti_ex_item_get_enable(noti_ex_item_h handle, bool *enable) {`
- L2552: `extern "C" EXPORT_API int noti_ex_item_add_receiver(noti_ex_item_h handle, const char *receiver_group) {`
- L2567: `extern "C" EXPORT_API int noti_ex_item_remove_receiver(noti_ex_item_h handle, const char *receiver_group) {`
- L2582: `extern "C" EXPORT_API int noti_ex_item_get_receiver_list(noti_ex_item_h handle, char ***receiver_list, int *count) {`
- L2622: `extern "C" EXPORT_API int noti_ex_item_set_policy(noti_ex_item_h handle, int policy) {`
- L2637: `extern "C" EXPORT_API int noti_ex_item_get_policy(noti_ex_item_h handle, int *policy) {`
- L2652: `extern "C" EXPORT_API int noti_ex_item_get_channel(noti_ex_item_h handle, char **channel) {`
- L2671: `extern "C" EXPORT_API int noti_ex_item_set_channel(noti_ex_item_h handle, const char *channel) {`
- L2686: `extern "C" EXPORT_API int noti_ex_item_set_led_info(noti_ex_item_h handle, noti_ex_led_info_h led) {`
- L2707: `extern "C" EXPORT_API int noti_ex_item_get_led_info(noti_ex_item_h handle, noti_ex_led_info_h *led) {`
- L2725: `extern "C" EXPORT_API int noti_ex_item_set_sound_path(noti_ex_item_h handle, const char *path) {`
- L2743: `extern "C" EXPORT_API int noti_ex_item_set_vibration_path(noti_ex_item_h handle, const char *path) {`
- L2761: `extern "C" EXPORT_API int noti_ex_item_get_sound_path(noti_ex_item_h handle, char **path) {`
- L2779: `extern "C" EXPORT_API int noti_ex_item_get_vibration_path(noti_ex_item_h handle, char **path) {`
- L2797: `extern "C" EXPORT_API int noti_ex_item_get_info(noti_ex_item_h handle, noti_ex_item_info_h *info) {`
- L2815: `extern "C" EXPORT_API int noti_ex_item_get_sender_app_id(noti_ex_item_h handle, char **id) {`
- L2833: `extern "C" EXPORT_API int noti_ex_item_get_tag(noti_ex_item_h handle, char **tag) {`
- L2851: `extern "C" EXPORT_API int noti_ex_item_set_tag(noti_ex_item_h handle, const char *tag) {`
- L2869: `extern "C" EXPORT_API int noti_ex_item_get_ongoing_state(noti_ex_item_h handle, bool* ongoing) {`
- L2885: `extern "C" EXPORT_API int noti_ex_item_set_ongoing_state(noti_ex_item_h handle, bool ongoing) {`
- L2901: `extern "C" EXPORT_API int noti_ex_item_check_type_exist(noti_ex_item_h handle, int type, bool* exist) {`
- L2917: `extern "C" EXPORT_API int noti_ex_item_get_main_type(noti_ex_item_h handle, int* type) {`
- L2933: `extern "C" EXPORT_API int noti_ex_item_set_main_type(noti_ex_item_h handle, const char* id, int type) {`
- L2951: `extern "C" EXPORT_API int noti_ex_item_find_by_main_type(noti_ex_item_h handle, int type, noti_ex_item_h* item) {`
- L2979: `extern "C" EXPORT_API int noti_ex_item_get_extension_data(noti_ex_item_h handle, const char *key, bundle **value) {`
- L3000: `extern "C" EXPORT_API int noti_ex_item_set_extension_data(noti_ex_item_h handle, const char *key, bundle *value) {`
- L3018: `extern "C" EXPORT_API int noti_ex_manager_create(noti_ex_manager_h *handle, const char *receiver_group, noti_ex_manager_events_s event_callbacks, void *data) {`
- L3049: `extern "C" EXPORT_API int noti_ex_manager_destroy(noti_ex_manager_h handle) {`
- L3062: `extern "C" EXPORT_API int noti_ex_manager_get(noti_ex_manager_h handle, noti_ex_item_h **items, int *count) {`
- L3101: `extern "C" EXPORT_API int noti_ex_manager_get_by_channel( noti_ex_manager_h handle, char* channel, noti_ex_item_h** items, int* count) {`
- L3143: `extern "C" EXPORT_API int noti_ex_manager_update(noti_ex_manager_h handle, noti_ex_item_h noti, int *request_id) {`
- L3168: `extern "C" EXPORT_API int noti_ex_manager_delete(noti_ex_manager_h handle, noti_ex_item_h noti, int *request_id) {`
- L3194: `extern "C" EXPORT_API int noti_ex_manager_delete_all(noti_ex_manager_h handle, int *request_id) {`
- L3213: `extern "C" EXPORT_API int noti_ex_manager_delete_by_channel( noti_ex_manager_h handle, const char* channel, int* request_id) {`
- L3233: `extern "C" EXPORT_API int noti_ex_manager_delete_by_appid( noti_ex_manager_h handle, const char* app_id, int* request_id) {`
- L3254: `extern "C" EXPORT_API int noti_ex_manager_hide(noti_ex_manager_h handle, noti_ex_item_h noti, int *request_id) {`
- L3279: `extern "C" EXPORT_API int noti_ex_manager_find_by_root_id( noti_ex_manager_h handle, const char *root_id, noti_ex_item_h *item) {`
- L3304: `extern "C" EXPORT_API int noti_ex_manager_send_error(noti_ex_manager_h handle, noti_ex_event_info_h info, noti_ex_error_e error) {`
- L3325: `extern "C" EXPORT_API int noti_ex_manager_get_notification_count( noti_ex_manager_h handle, int *count) {`
- L3344: `extern "C" EXPORT_API int noti_ex_item_progress_create(noti_ex_item_h *handle, const char *id, float min, float current, float max) {`
- L3371: `extern "C" EXPORT_API int noti_ex_item_progress_get_current( noti_ex_item_h handle, float *current) {`
- L3392: `extern "C" EXPORT_API int noti_ex_item_progress_set_current( noti_ex_item_h handle, float current) {`
- L3413: `extern "C" EXPORT_API int noti_ex_item_progress_get_min(noti_ex_item_h handle, float *min) {`
- L3434: `extern "C" EXPORT_API int noti_ex_item_progress_get_max(noti_ex_item_h handle, float *max) {`
- L3455: `extern "C" EXPORT_API int noti_ex_item_progress_get_type(noti_ex_item_h handle, int* type) {`
- L3476: `extern "C" EXPORT_API int noti_ex_item_progress_set_type(noti_ex_item_h handle, int type) {`
- L3497: `extern "C" EXPORT_API int noti_ex_reporter_create(noti_ex_reporter_h *handle, noti_ex_reporter_events_s event_callbacks, void *data) {`
- L3522: `extern "C" EXPORT_API int noti_ex_reporter_destroy(noti_ex_reporter_h handle) {`
- L3535: `extern "C" EXPORT_API int noti_ex_reporter_send_error(noti_ex_reporter_h handle, noti_ex_event_info_h info, noti_ex_error_e error) {`
- L3556: `extern "C" EXPORT_API int noti_ex_reporter_post(noti_ex_reporter_h handle, noti_ex_item_h noti, int *request_id) {`
- L3583: `extern "C" EXPORT_API int noti_ex_reporter_post_list(noti_ex_reporter_h handle, noti_ex_item_h *noti_list, int count, int *request_id) {`
- L3609: `extern "C" EXPORT_API int noti_ex_reporter_update(noti_ex_reporter_h handle, noti_ex_item_h noti, int *request_id) {`
- L3636: `extern "C" EXPORT_API int noti_ex_reporter_update_list( noti_ex_reporter_h handle, noti_ex_item_h *noti_list, int count, int *request_id) {`
- L3663: `extern "C" EXPORT_API int noti_ex_reporter_delete(noti_ex_reporter_h handle, noti_ex_item_h noti, int *request_id) {`
- L3690: `extern "C" EXPORT_API int noti_ex_reporter_delete_list( noti_ex_reporter_h handle, noti_ex_item_h *noti_list, int count, int *request_id) {`
- L3719: `extern "C" EXPORT_API int noti_ex_reporter_delete_all( noti_ex_reporter_h handle, int *request_id) {`
- L3742: `extern "C" EXPORT_API int noti_ex_reporter_delete_by_channel( noti_ex_reporter_h handle, const char* channel, int* request_id) {`
- L3765: `extern "C" EXPORT_API int noti_ex_reporter_find_by_root_id( noti_ex_reporter_h handle, const char *root_id, noti_ex_item_h *item) {`
- L3790: `extern "C" EXPORT_API int noti_ex_reporter_find_by_channel(noti_ex_reporter_h handle, const char *channel, noti_ex_item_h **noti_list, int *count) {`
- L3836: `extern "C" EXPORT_API int noti_ex_reporter_find_all(noti_ex_reporter_h handle, noti_ex_item_h **noti_list, int *count) {`
- L3881: `extern "C" EXPORT_API int noti_ex_reporter_get_count_by_channel( noti_ex_reporter_h handle, const char *channel, int *count) {`
- L3902: `extern "C" EXPORT_API int noti_ex_item_text_create(noti_ex_item_h *handle, const char *id, const char *text, const char *hyperlink) {`
- L3933: `extern "C" EXPORT_API int noti_ex_item_text_set_contents(noti_ex_item_h handle, const char *contents) {`
- L3954: `extern "C" EXPORT_API int noti_ex_item_text_get_contents(noti_ex_item_h handle, char **contents) {`
- L3987: `extern "C" EXPORT_API int noti_ex_item_text_get_hyperlink( noti_ex_item_h handle, char **hyper_link) {`
- L4016: `extern "C" EXPORT_API int noti_ex_item_text_set_multi_language( noti_ex_item_h handle, noti_ex_multi_lang_h multi) {`
- L4046: `extern "C" EXPORT_API int noti_ex_item_time_create(noti_ex_item_h *handle, const char *id, time_t time) {`
- L4077: `extern "C" EXPORT_API int noti_ex_item_time_get_time(noti_ex_item_h handle, time_t *time) {`
- L4097: `extern "C" EXPORT_API int noti_ex_item_time_set_time(noti_ex_item_h handle, time_t time) {`
- L4117: `extern "C" EXPORT_API int noti_ex_action_visibility_create( noti_ex_action_h *handle, const char *extra) {`
- L4143: `extern "C" EXPORT_API int noti_ex_action_visibility_set(noti_ex_action_h handle, const char *id, bool visible) {`
- L4161: `extern "C" EXPORT_API int noti_ex_multi_lang_create(noti_ex_multi_lang_h* handle, const char* msgid, const char* format, ...) {`
- L4212: `extern "C" EXPORT_API int noti_ex_multi_lang_destroy(noti_ex_multi_lang_h handle) {`
- L4227: `extern "C" EXPORT_API int noti_ex_item_get_private_id( noti_ex_item_h handle, int64_t* private_id) {`
- L4244: `extern "C" EXPORT_API int noti_ex_item_free_string_list(char** list, int count) {`
- L4261: `extern "C" EXPORT_API int noti_ex_item_group_remove_children(noti_ex_item_h handle) {`
- L4280: `extern "C" EXPORT_API int noti_ex_item_icon_create(noti_ex_item_h *handle, const char *id, const char *icon_path) {`
- L4306: `extern "C" EXPORT_API int noti_ex_item_icon_get_icon_path(noti_ex_item_h handle, char **icon_path) {`


### `src/notification-ex/text_item.h` — Public — 1 APIs

**Classes**

- L38: `class EXPORT_API TextItem : public AbstractItem {`


### `src/notification-ex/time_item.h` — Public — 1 APIs

**Classes**

- L36: `class EXPORT_API TimeItem : public AbstractItem {`


### `src/notification-ex/visibility_action.h` — Public — 1 APIs

**Classes**

- L32: `class EXPORT_API VisibilityAction : public AbstractAction {`


### `src/notification/src/notification.c` — Public — 57 APIs

**Functions**

- L96: `EXPORT_API int notification_set_image(notification_h noti, notification_image_type_e type, const char *image_path)`
- L156: `EXPORT_API int notification_get_image(notification_h noti, notification_image_type_e type, char **image_path)`
- L196: `EXPORT_API int notification_set_time(notification_h noti, time_t input_time)`
- L209: `EXPORT_API int notification_get_time(notification_h noti, time_t *ret_time)`
- L219: `EXPORT_API int notification_get_insert_time(notification_h noti, time_t *ret_time)`
- L230: `EXPORT_API int notification_set_text(notification_h noti, notification_text_type_e type, const char *text, const char *key, int args_type, ...)`
- L443: `EXPORT_API int notification_get_text(notification_h noti, notification_text_type_e type, char **text)`
- L793: `EXPORT_API int notification_set_text_domain(notification_h noti, const char *domain, const char *dir)`
- L813: `EXPORT_API int notification_get_text_domain(notification_h noti, char **domain, char **dir)`
- L829: `EXPORT_API int notification_set_time_to_text(notification_h noti, notification_text_type_e type, time_t time)`
- L852: `EXPORT_API int notification_get_time_from_text(notification_h noti, notification_text_type_e type, time_t *time)`
- L883: `EXPORT_API int notification_set_sound(notification_h noti, notification_sound_type_e type, const char *path)`
- L932: `EXPORT_API int notification_get_sound(notification_h noti, notification_sound_type_e *type, const char **path)`
- L949: `EXPORT_API int notification_set_vibration(notification_h noti, notification_vibration_type_e type, const char *path)`
- L998: `EXPORT_API int notification_get_vibration(notification_h noti, notification_vibration_type_e *type, const char **path)`
- L1014: `EXPORT_API int notification_set_led(notification_h noti, notification_led_op_e operation, int led_argb)`
- L1034: `EXPORT_API int notification_get_led(notification_h noti, notification_led_op_e *operation, int *led_argb)`
- L1051: `EXPORT_API int notification_set_led_time_period(notification_h noti, int on_ms, int off_ms)`
- L1063: `EXPORT_API int notification_get_led_time_period(notification_h noti, int *on_ms, int *off_ms)`
- L1077: `EXPORT_API int notification_set_launch_option(notification_h noti, notification_launch_option_type type, void *option)`
- L1106: `EXPORT_API int notification_get_launch_option(notification_h noti, notification_launch_option_type type, void *option)`
- L1153: `EXPORT_API int notification_set_event_handler(notification_h noti, notification_event_type_e event_type, app_control_h event_handler)`
- L1186: `EXPORT_API int notification_get_event_handler(notification_h noti, notification_event_type_e event_type, app_control_h *event_handler)`
- L1245: `EXPORT_API int notification_set_property(notification_h noti, int flags)`
- L1256: `EXPORT_API int notification_get_property(notification_h noti, int *flags)`
- L1267: `EXPORT_API int notification_set_display_applist(notification_h noti, int applist)`
- L1281: `EXPORT_API int notification_get_display_applist(notification_h noti, int *applist)`
- L1292: `EXPORT_API int notification_set_size(notification_h noti, double size)`
- L1303: `EXPORT_API int notification_get_size(notification_h noti, double *size)`
- L1314: `EXPORT_API int notification_set_progress(notification_h noti, double percentage)`
- L1325: `EXPORT_API int notification_get_progress(notification_h noti, double *percentage)`
- L1336: `EXPORT_API int notification_get_pkgname(notification_h noti, char **pkgname)`
- L1350: `EXPORT_API int notification_set_layout(notification_h noti, notification_ly_type_e layout)`
- L1361: `EXPORT_API int notification_get_layout(notification_h noti, notification_ly_type_e *layout)`
- L1372: `EXPORT_API int notification_get_type(notification_h noti, notification_type_e *type)`
- L1383: `EXPORT_API int notification_post(notification_h noti)`
- L1388: `EXPORT_API int notification_update(notification_h noti)`
- L1393: `EXPORT_API int notification_delete_all(notification_type_e type)`
- L1398: `EXPORT_API int notification_delete(notification_h noti)`
- L1631: `EXPORT_API notification_h notification_create(notification_type_e type)`
- L1636: `EXPORT_API notification_h notification_load_by_tag(const char *tag)`
- L1641: `EXPORT_API int notification_clone(notification_h noti, notification_h *clone)`
- L1776: `EXPORT_API int notification_free(notification_h noti)`
- L1875: `EXPORT_API int notification_set_tag(notification_h noti, const char *tag)`
- L1890: `EXPORT_API int notification_get_tag(notification_h noti, const char **tag)`
- L1907: `EXPORT_API int notification_set_ongoing_flag(notification_h noti, bool ongoing_flag)`
- L1917: `EXPORT_API int notification_get_ongoing_flag(notification_h noti, bool *ongoing_flag)`
- L1927: `EXPORT_API int notification_add_button(notification_h noti, notification_button_index_e button_index)`
- L1937: `EXPORT_API int notification_remove_button(notification_h noti, notification_button_index_e button_index)`
- L1952: `EXPORT_API int notification_set_auto_remove(notification_h noti, bool auto_remove)`
- L1962: `EXPORT_API int notification_get_auto_remove(notification_h noti, bool *auto_remove)`
- L1972: `EXPORT_API int notification_save_as_template(notification_h noti, const char *template_name)`
- L1982: `EXPORT_API notification_h notification_create_from_template(const char *template_name)`
- L2006: `EXPORT_API int notification_get_noti_block_state(notification_block_state_e *state)`
- L2040: `EXPORT_API int notification_set_text_input(notification_h noti, int text_input_max_length)`
- L2050: `EXPORT_API int notification_set_extension_image_size(notification_h noti, int height)`
- L2060: `EXPORT_API int notification_get_extension_image_size(notification_h noti, int *height)`


### `src/notification/src/notification_db.c` — Public — 7 APIs

**Functions**

- L85: `EXPORT_API int notification_db_init(void)`
- L126: `EXPORT_API sqlite3 *notification_db_open()`
- L154: `EXPORT_API int notification_db_close(sqlite3 **db)`
- L174: `EXPORT_API int notification_db_exec(sqlite3 *db, const char *query, int *num_changes)`
- L208: `EXPORT_API char *notification_db_column_text(sqlite3_stmt *stmt, int col)`
- L219: `EXPORT_API bundle *notification_db_column_bundle(sqlite3_stmt *stmt, int col)`
- L374: `EXPORT_API int notification_upgrade_db(void)`


### `src/notification/src/notification_error.c` — Public — 1 APIs

**Functions**

- L37: `EXPORT_API GQuark notification_error_quark(void)`


### `src/notification/src/notification_internal.c` — Internal — 105 APIs

**Functions**

- L300: `EXPORT_API int notification_add_deferred_task( void (*deferred_task_cb)(void *data), void *user_data)`
- L313: `EXPORT_API int notification_del_deferred_task( void (*deferred_task_cb)(void *data))`
- L328: `EXPORT_API int notification_resister_changed_cb_for_uid( notification_changed_cb callback, void *user_data, uid_t uid)`
- L373: `EXPORT_API int notification_resister_changed_cb( notification_changed_cb callback, void *user_data)`
- L393: `EXPORT_API int notification_unresister_changed_cb_for_uid( notification_changed_cb callback, uid_t uid)`
- L438: `EXPORT_API int notification_unresister_changed_cb( notification_changed_cb callback)`
- L444: `EXPORT_API int notification_update_progress(notification_h noti, int priv_id, double progress)`
- L483: `EXPORT_API int notification_update_size(notification_h noti, int priv_id, double size)`
- L520: `EXPORT_API int notification_update_content(notification_h noti, int priv_id, const char *content)`
- L554: `EXPORT_API int notification_set_icon(notification_h noti, const char *icon_path)`
- L563: `EXPORT_API int notification_get_icon(notification_h noti, char **icon_path)`
- L580: `EXPORT_API int notification_translate_localized_text(notification_h noti)`
- L626: `EXPORT_API int notification_set_title(notification_h noti, const char *title, const char *loc_title)`
- L637: `EXPORT_API int notification_get_title(notification_h noti, char **title, char **loc_title)`
- L658: `EXPORT_API int notification_set_content(notification_h noti, const char *content, const char *loc_content)`
- L669: `EXPORT_API int notification_get_content(notification_h noti, char **content, char **loc_content)`
- L690: `EXPORT_API int notification_set_application(notification_h noti, const char *app_id)`
- L706: `EXPORT_API int notification_get_application(notification_h noti, char **app_id)`
- L722: `EXPORT_API int notification_set_args(notification_h noti, bundle *args, bundle *group_args)`
- L746: `EXPORT_API int notification_get_args(notification_h noti, bundle **args, bundle **group_args)`
- L784: `EXPORT_API int notification_get_grouping_list(notification_type_e type, int count, notification_list_h *list)`
- L792: `EXPORT_API int notification_delete_group_by_group_id(const char *app_id, notification_type_e type, int group_id)`
- L840: `EXPORT_API int notification_delete_group_by_priv_id(const char *app_id, notification_type_e type, int priv_id)`
- L882: `EXPORT_API int notification_get_count(notification_type_e type, const char *app_id, int group_id, int priv_id, int *count)`
- L906: `EXPORT_API int notification_clear(notification_type_e type)`
- L911: `EXPORT_API int notification_op_get_data(notification_op *noti_op, notification_op_data_type_e type, void *data)`
- L942: `EXPORT_API int notification_set_pkgname(notification_h noti, const char *pkgname)`
- L950: `EXPORT_API int notification_set_app_id(notification_h noti, const char *app_id)`
- L995: `EXPORT_API int notification_delete_all_by_type(const char *app_id, notification_type_e type)`
- L1029: `EXPORT_API int notification_delete_by_priv_id(const char *app_id, notification_type_e type, int priv_id)`
- L1036: `EXPORT_API int notification_set_execute_option(notification_h noti, notification_execute_type_e type, const char *text, const char *key, bundle *service_handle)`
- L1118: `EXPORT_API int notification_get_id(notification_h noti, int *group_id, int *priv_id)`
- L1139: `EXPORT_API int notification_set_priv_id(notification_h noti, int priv_id)`
- L1173: `EXPORT_API notification_h notification_load(char *app_id, int priv_id)`
- L1181: `EXPORT_API notification_h notification_new(notification_type_e type, int group_id, int priv_id)`
- L1193: `EXPORT_API int notification_get_execute_option(notification_h noti, notification_execute_type_e type, const char **text, bundle **service_handle)`
- L1262: `EXPORT_API int notification_insert_for_uid(notification_h noti, int *priv_id, uid_t uid)`
- L1306: `EXPORT_API int notification_insert(notification_h noti, int *priv_id)`
- L1312: `EXPORT_API int notification_update_async_for_uid(notification_h noti, void (*result_cb)(int priv_id, int result, void *data), void *user_data, uid_t uid)`
- L1331: `EXPORT_API int notification_update_async(notification_h noti, void (*result_cb)(int priv_id, int result, void *data), void *user_data)`
- L1339: `EXPORT_API int notification_register_detailed_changed_cb_for_uid( notification_detailed_changed_cb callback, void *user_data, uid_t uid)`
- L1385: `EXPORT_API int notification_register_detailed_changed_cb( notification_detailed_changed_cb callback, void *user_data)`
- L1405: `EXPORT_API int notification_unregister_detailed_changed_cb_for_uid( notification_detailed_changed_cb callback, void *user_data, uid_t uid)`
- L1452: `EXPORT_API int notification_unregister_detailed_changed_cb( notification_detailed_changed_cb callback, void *user_data)`
- L1461: `EXPORT_API int notification_is_service_ready(void)`
- L1472: `EXPORT_API int notification_set_uid(notification_h noti, uid_t uid)`
- L1482: `EXPORT_API int notification_get_uid(notification_h noti, uid_t *uid)`
- L1560: `EXPORT_API int notification_post_for_uid(notification_h noti, uid_t uid)`
- L1610: `EXPORT_API int notification_update_for_uid(notification_h noti, uid_t uid)`
- L1635: `EXPORT_API int notification_delete_for_uid(notification_h noti, uid_t uid)`
- L1649: `EXPORT_API int notification_delete_all_for_uid(notification_type_e type, uid_t uid)`
- L1671: `EXPORT_API notification_h notification_load_by_tag_for_uid(const char *tag, uid_t uid)`
- L1705: `EXPORT_API notification_h notification_create_from_package_template(const char *app_id, const char *template_name)`
- L1730: `EXPORT_API int notification_set_default_button(notification_h noti, notification_button_index_e index)`
- L1743: `EXPORT_API int notification_get_default_button(notification_h noti, notification_button_index_e *index)`
- L1753: `EXPORT_API int notification_get_ongoing_value_type(notification_h noti, notification_ongoing_value_type_e *type)`
- L1763: `EXPORT_API int notification_set_ongoing_value_type(notification_h noti, notification_ongoing_value_type_e type)`
- L1776: `EXPORT_API int notification_get_ongoing_time(notification_h noti, int *current, int *duration)`
- L1787: `EXPORT_API int notification_set_ongoing_time(notification_h noti, int current, int duration)`
- L1801: `EXPORT_API int notification_get_hide_timeout(notification_h noti, int *timeout)`
- L1811: `EXPORT_API int notification_set_hide_timeout(notification_h noti, int timeout)`
- L1821: `EXPORT_API int notification_get_delete_timeout(notification_h noti, int *timeout)`
- L1831: `EXPORT_API int notification_set_delete_timeout(notification_h noti, int timeout)`
- L1841: `EXPORT_API int notification_get_text_input_max_length(notification_h noti, int *text_input_max_length)`
- L1853: `EXPORT_API int notification_post_with_event_cb_for_uid(notification_h noti, event_handler_cb cb, void *userdata, uid_t uid)`
- L1928: `EXPORT_API int notification_post_with_event_cb(notification_h noti, event_handler_cb cb, void *userdata)`
- L1933: `EXPORT_API int notification_send_event(notification_h noti, int event_type)`
- L1961: `EXPORT_API int notification_send_event_by_priv_id(int priv_id, int event_type)`
- L1984: `EXPORT_API int notification_get_event_flag(notification_h noti, bool *flag)`
- L1994: `EXPORT_API int notification_check_event_receiver_available(notification_h noti, bool *available)`
- L2023: `EXPORT_API int notification_set_extention_data(notification_h noti, const char *key, bundle *value)`
- L2028: `EXPORT_API int notification_set_extension_data(notification_h noti, const char *key, bundle *value)`
- L2062: `EXPORT_API int notification_get_extention_data(notification_h noti, const char *key, bundle **value)`
- L2067: `EXPORT_API int notification_get_extension_data(notification_h noti, const char *key, bundle **value)`
- L2097: `EXPORT_API int notification_set_extension_event_handler(notification_h noti, notification_event_type_extension_e event, app_control_h event_handler)`
- L2162: `EXPORT_API int notification_get_extension_event_handler(notification_h noti, notification_event_type_extension_e event, app_control_h *event_handler)`
- L2224: `EXPORT_API int notification_get_all_count_for_uid(notification_type_e type, int *count, uid_t uid)`
- L2249: `EXPORT_API int notification_get_all_count(notification_type_e type, int *count)`
- L2254: `EXPORT_API int notification_set_app_label(notification_h noti, char *label)`
- L2267: `EXPORT_API int notification_get_app_label(notification_h noti, char **label)`
- L2310: `EXPORT_API int notification_set_indirect_request(notification_h noti, pid_t pid, uid_t uid)`
- L2364: `EXPORT_API int notification_delete_by_display_applist(int display_applist)`
- L2369: `EXPORT_API int notification_set_check_box(notification_h noti, bool flag, bool checked)`
- L2383: `EXPORT_API int notification_get_check_box(notification_h noti, bool *flag, bool *checked)`
- L2397: `EXPORT_API int notification_set_check_box_checked(notification_h noti, bool checked)`
- L2410: `EXPORT_API int notification_get_check_box_checked(notification_h noti, bool *checked)`
- L2428: `EXPORT_API int notification_register_do_not_disturb_app(disturb_cb callback, void *user_data)`
- L2461: `EXPORT_API int notification_unregister_do_not_disturb_app(void)`
- L2506: `EXPORT_API int notification_set_pairing_type(notification_h noti, bool pairing)`
- L2534: `EXPORT_API int notification_get_pairing_type(notification_h noti, bool *pairing)`
- L2560: `EXPORT_API int notification_set_channel_name(notification_h noti, const char *channel_name)`
- L2578: `EXPORT_API int notification_get_channel_name(notification_h noti, const char **channel_name)`
- L2622: `EXPORT_API int notification_channel_create(const char *channel_name, notification_channel_h *channel)`
- L2650: `EXPORT_API void notification_channel_free(notification_channel_h channel)`
- L2670: `EXPORT_API int notification_channel_add(notification_channel_h channel)`
- L2698: `EXPORT_API int notification_channel_remove(notification_channel_h channel)`
- L2725: `EXPORT_API int notification_channel_update(notification_channel_h channel)`
- L2753: `EXPORT_API int notification_channel_get_by_name(const char *channel_name, notification_channel_h *channel)`
- L2804: `EXPORT_API int notification_channel_set_blockable( notification_channel_h channel,bool blockable)`
- L2821: `EXPORT_API int notification_channel_get_blockable( notification_channel_h channel, bool *blockable)`
- L2838: `EXPORT_API int notification_channel_set_block( notification_channel_h channel, bool block)`
- L2855: `EXPORT_API int notification_channel_get_block( notification_channel_h channel, bool *block)`
- L2872: `EXPORT_API int notification_channel_get_name(notification_channel_h channel, const char **channel_name)`
- L2889: `EXPORT_API int notification_channel_clone(notification_channel_h channel, notification_channel_h *clone)`
- L2919: `EXPORT_API int notification_channel_foreach(const char *app_id, notification_channel_foreach_cb cb, void *user_data)`


### `src/notification/src/notification_internal_tidl.c` — Internal — 8 APIs

**Functions**

- L57: `EXPORT_API int make_empty_notification(void *notihandle)`
- L320: `EXPORT_API int make_notification_from_noti(void *notihandle, notification_h noti, bool translate)`
- L606: `EXPORT_API int make_noti_from_notification(notification_h *noti, void *notihandle)`
- L1163: `EXPORT_API int make_setting_from_noti_system_setting( notification_system_setting_h *setting, void *settinghandle)`
- L1210: `EXPORT_API int make_dnd_allow_exception_from_exception(void *exception_handle, dnd_allow_exception_h dnd_allow_exception)`
- L1231: `EXPORT_API int make_noti_system_setting_from_setting(void *settinghandle, notification_system_setting_h setting)`
- L1312: `EXPORT_API int make_setting_from_noti_setting( notification_setting_h setting, void *settinghandle)`
- L1386: `EXPORT_API int make_noti_setting_from_setting( void *settinghandle, notification_setting_h setting)`


### `src/notification/src/notification_ipc.c` — Public — 2 APIs

**Functions**

- L62: `EXPORT_API GVariant *notification_ipc_make_gvariant_from_noti(notification_h noti, bool translate)`
- L342: `EXPORT_API int notification_ipc_make_noti_from_gvariant(notification_h noti, GVariant *variant) {`


### `src/notification/src/notification_list.c` — Public — 15 APIs

**Functions**

- L56: `EXPORT_API notification_list_h notification_list_get_head(notification_list_h list)`
- L75: `EXPORT_API notification_list_h notification_list_get_tail(notification_list_h list)`
- L94: `EXPORT_API notification_list_h notification_list_get_prev(notification_list_h list)`
- L110: `EXPORT_API notification_list_h notification_list_get_next(notification_list_h list)`
- L126: `EXPORT_API notification_h notification_list_get_data(notification_list_h list)`
- L142: `EXPORT_API int notification_list_get_count(notification_list_h list)`
- L164: `EXPORT_API notification_list_h notification_list_append(notification_list_h list, notification_h noti)`
- L210: `EXPORT_API notification_list_h notification_list_remove(notification_list_h list, notification_h noti)`
- L251: `EXPORT_API int notification_get_list_for_uid(notification_type_e type, int count, notification_list_h *list, uid_t uid)`
- L271: `EXPORT_API int notification_get_list(notification_type_e type, int count, notification_list_h *list)`
- L278: `EXPORT_API int notification_get_list_by_page_for_uid(notification_type_e type, int page_number, int count_per_page, notification_list_h *list, uid_t uid)`
- L317: `EXPORT_API int notification_get_list_by_page(notification_type_e type, int page_number, int count_per_page, notification_list_h *list)`
- L324: `EXPORT_API int notification_get_detail_list_for_uid(const char *app_id, int group_id, int priv_id, int count, notification_list_h *list, uid_t uid)`
- L348: `EXPORT_API int notification_get_detail_list(const char *app_id, int group_id, int priv_id, int count, notification_list_h *list)`
- L358: `EXPORT_API int notification_free_list(notification_list_h list)`


### `src/notification/src/notification_noti.c` — Public — 24 APIs

**Functions**

- L1050: `EXPORT_API int notification_noti_insert(notification_h noti)`
- L1137: `EXPORT_API int notification_noti_get_by_priv_id(notification_h noti, int priv_id)`
- L1165: `EXPORT_API int notification_noti_get_by_tag(notification_h noti, char *app_id, char *tag, uid_t uid)`
- L1193: `EXPORT_API int notification_noti_update(notification_h noti)`
- L1273: `EXPORT_API int notification_noti_delete_all(notification_type_e type, const char *app_id, int *deleted_num, int **deleted_list, uid_t uid)`
- L1407: `EXPORT_API int notification_noti_delete_by_priv_id(const char *app_id, int priv_id)`
- L1440: `EXPORT_API int notification_noti_delete_by_priv_id_get_changes(const char *app_id, int priv_id, int *num_changes, uid_t uid)`
- L1475: `EXPORT_API int notification_noti_delete_by_display_applist(int display_applist, int *deleted_num, notification_deleted_list_info_s **deleted_list, uid_t uid)`
- L1597: `EXPORT_API int notification_noti_get_count(notification_type_e type, const char *app_id, int group_id, int priv_id, int *count, uid_t uid)`
- L1733: `EXPORT_API int notification_noti_get_all_count(notification_type_e type, int *count, uid_t uid)`
- L1800: `EXPORT_API int notification_noti_get_grouping_list(notification_type_e type, int page_number, int count_per_page, notification_list_h *list, int *list_count, uid_t uid)`
- L1882: `EXPORT_API int notification_noti_get_detail_list(const char *app_id, int group_id, int priv_id, int count, notification_list_h *list, uid_t uid)`
- L1962: `EXPORT_API int notification_noti_check_tag(notification_h noti)`
- L2029: `EXPORT_API int notification_noti_check_count_for_template(notification_h noti, int *count)`
- L2085: `EXPORT_API int notification_noti_add_template(notification_h noti, char *template_name)`
- L2151: `EXPORT_API int notification_noti_get_package_template(notification_h noti, char *app_id, char *template_name)`
- L2176: `EXPORT_API int notification_noti_delete_template(const char *pkg_id)`
- L2211: `EXPORT_API void notification_noti_init_data(void)`
- L2240: `EXPORT_API int notification_noti_check_limit(notification_h noti, uid_t uid, GList **list)`
- L2320: `EXPORT_API int notification_noti_get_channel(const char *app_id, const char *channel_name, int *blockable, int *is_blocked)`
- L2385: `EXPORT_API int notification_noti_insert_channel(const char *app_id, const char *channel_name, int blockable, int is_blocked)`
- L2426: `EXPORT_API int notification_noti_delete_channel(const char *app_id, const char *channel_name)`
- L2466: `EXPORT_API int notification_noti_update_channel(const char *app_id, const char *channel_name, int blockable, int is_blocked)`
- L2507: `EXPORT_API int notification_noti_get_channel_list(const char *app_id, GList **channel_list)`


### `src/notification/src/notification_ongoing.c` — Public — 2 APIs

**Functions**

- L30: `EXPORT_API int notification_ongoing_update_cb_set(notification_ongoing_update_cb callback, void *user_data)`
- L39: `EXPORT_API int notification_ongoing_update_cb_unset(void)`


### `src/notification/src/notification_setting.c` — Public — 50 APIs

**Functions**

- L54: `EXPORT_API int notification_setting_get_setting_array_for_uid(notification_setting_h *setting_array, int *count, uid_t uid)`
- L64: `EXPORT_API int notification_setting_get_setting_array(notification_setting_h *setting_array, int *count)`
- L69: `EXPORT_API int notification_setting_get_setting_by_appid_for_uid(const char *app_id, notification_setting_h *setting, uid_t uid)`
- L81: `EXPORT_API int notification_setting_get_setting_by_package_name(const char *package_name, notification_setting_h *setting)`
- L88: `EXPORT_API int notification_setting_get_setting(notification_setting_h *setting)`
- L106: `EXPORT_API int notification_setting_get_package_name(notification_setting_h setting, char **value)`
- L125: `EXPORT_API int notification_setting_get_appid(notification_setting_h setting, char **app_id)`
- L144: `EXPORT_API int notification_setting_get_allow_to_notify(notification_setting_h setting, bool *value)`
- L156: `EXPORT_API int notification_setting_set_allow_to_notify(notification_setting_h setting, bool value)`
- L168: `EXPORT_API int notification_setting_get_do_not_disturb_except(notification_setting_h setting, bool *value)`
- L180: `EXPORT_API int notification_setting_set_do_not_disturb_except(notification_setting_h setting, bool value)`
- L193: `EXPORT_API int notification_setting_get_visibility_class(notification_setting_h setting, int *value)`
- L205: `EXPORT_API int notification_setting_set_visibility_class(notification_setting_h setting, int value)`
- L218: `EXPORT_API int notification_setting_get_pop_up_notification(notification_setting_h setting, bool *value)`
- L229: `EXPORT_API int notification_setting_set_pop_up_notification(notification_setting_h setting, bool value)`
- L240: `EXPORT_API int notification_setting_get_lock_screen_content(notification_setting_h setting, lock_screen_content_level_e *level)`
- L252: `EXPORT_API int notification_setting_set_lock_screen_content(notification_setting_h setting, lock_screen_content_level_e level)`
- L264: `EXPORT_API int notification_setting_get_app_disabled(notification_setting_h setting, bool *value)`
- L277: `EXPORT_API int notification_setting_update_setting_for_uid(notification_setting_h setting, uid_t uid)`
- L287: `EXPORT_API int notification_setting_update_setting(notification_setting_h setting)`
- L292: `EXPORT_API int notification_setting_free_notification(notification_setting_h setting)`
- L526: `EXPORT_API int notification_setting_refresh_setting_table(uid_t uid)`
- L577: `EXPORT_API int notification_setting_insert_package_for_uid(const char *package_name, uid_t uid)`
- L582: `EXPORT_API int notification_setting_delete_package_for_uid(const char *package_name, uid_t uid)`
- L587: `EXPORT_API int notification_system_setting_load_system_setting_for_uid(notification_system_setting_h *system_setting, uid_t uid)`
- L597: `EXPORT_API int notification_system_setting_load_system_setting(notification_system_setting_h *system_setting)`
- L602: `EXPORT_API int notification_system_setting_update_system_setting_for_uid(notification_system_setting_h system_setting, uid_t uid)`
- L612: `EXPORT_API int notification_system_setting_update_system_setting(notification_system_setting_h system_setting)`
- L617: `EXPORT_API int notification_system_setting_free_system_setting(notification_system_setting_h system_setting)`
- L634: `EXPORT_API int notification_system_setting_get_do_not_disturb(notification_system_setting_h system_setting, bool *value)`
- L646: `EXPORT_API int notification_system_setting_set_do_not_disturb(notification_system_setting_h system_setting, bool value)`
- L658: `EXPORT_API int notification_system_setting_get_visibility_class(notification_system_setting_h system_setting, int *value)`
- L670: `EXPORT_API int notification_system_setting_set_visibility_class(notification_system_setting_h system_setting, int value)`
- L682: `EXPORT_API int notification_system_setting_dnd_schedule_get_enabled(notification_system_setting_h system_setting, bool *enabled)`
- L694: `EXPORT_API int notification_system_setting_dnd_schedule_set_enabled(notification_system_setting_h system_setting, bool enabled)`
- L706: `EXPORT_API int notification_system_setting_dnd_schedule_get_day(notification_system_setting_h system_setting, int *day)`
- L718: `EXPORT_API int notification_system_setting_dnd_schedule_set_day(notification_system_setting_h system_setting, int day)`
- L730: `EXPORT_API int notification_system_setting_dnd_schedule_get_start_time(notification_system_setting_h system_setting, int *hour, int *min)`
- L743: `EXPORT_API int notification_system_setting_dnd_schedule_set_start_time(notification_system_setting_h system_setting, int hour, int min)`
- L756: `EXPORT_API int notification_system_setting_dnd_schedule_get_end_time(notification_system_setting_h system_setting, int *hour, int *min)`
- L769: `EXPORT_API int notification_system_setting_dnd_schedule_set_end_time(notification_system_setting_h system_setting, int hour, int min)`
- L782: `EXPORT_API int notification_system_setting_get_lock_screen_content(notification_system_setting_h system_setting, lock_screen_content_level_e *level)`
- L794: `EXPORT_API int notification_system_setting_set_lock_screen_content(notification_system_setting_h system_setting, lock_screen_content_level_e level)`
- L821: `EXPORT_API int notification_system_setting_get_dnd_allow_exceptions(notification_system_setting_h system_setting, dnd_allow_exception_type_e type, int *value)`
- L843: `EXPORT_API int notification_system_setting_set_dnd_allow_exceptions(notification_system_setting_h system_setting, dnd_allow_exception_type_e type, int value)`
- L914: `EXPORT_API int notification_register_system_setting_dnd_changed_cb_for_uid(dnd_changed_cb callback, void *user_data, uid_t uid)`
- L960: `EXPORT_API int notification_register_system_setting_dnd_changed_cb(dnd_changed_cb callback, void *user_data)`
- L965: `EXPORT_API int notification_unregister_system_setting_dnd_changed_cb_for_uid(dnd_changed_cb callback, uid_t uid)`
- L1008: `EXPORT_API int notification_unregister_system_setting_dnd_changed_cb(dnd_changed_cb callback)`
- L1062: `EXPORT_API int notification_system_setting_init_system_setting_table(uid_t uid)`


### `src/notification/src/notification_setting_service.c` — Public — 13 APIs

**Functions**

- L89: `EXPORT_API int noti_setting_service_get_setting_by_app_id(const char *app_id, notification_setting_h *setting, uid_t uid)`
- L172: `EXPORT_API int noti_setting_get_setting_array(notification_setting_h *setting_array, int *count, uid_t uid)`
- L258: `EXPORT_API int noti_system_setting_load_system_setting(notification_system_setting_h *system_setting, uid_t uid)`
- L347: `EXPORT_API int notification_setting_db_update(const char *package_name, const char *app_id, int allow_to_notify, int do_not_disturb_except, int visibility_class, int pop_up_notification, int lock_scre...`
- L391: `EXPORT_API int notification_setting_db_update_system_setting(int do_not_disturb, int visibility_class, int dnd_schedule_enabled, int dnd_schedule_day, int dnd_start_hour, int dnd_start_min, int dnd_en...`
- L439: `EXPORT_API int notification_setting_db_update_do_not_disturb(int do_not_disturb, uid_t uid)`
- L474: `EXPORT_API int notification_system_setting_get_dnd_schedule_enabled_uid(uid_t **uids, int *count)`
- L541: `EXPORT_API int notification_get_dnd_and_allow_to_notify(const char *app_id, int *do_not_disturb, int *do_not_disturb_except, int *allow_to_notify, uid_t uid)`
- L638: `EXPORT_API int notification_system_setting_load_dnd_allow_exception(dnd_allow_exception_h *dnd_allow_exception, int *count, uid_t uid)`
- L710: `EXPORT_API int notification_system_setting_update_dnd_allow_exception(int type, int value, uid_t uid)`
- L749: `EXPORT_API int noti_system_setting_get_do_not_disturb(int *do_not_disturb, uid_t uid)`
- L803: `EXPORT_API int notification_setting_db_update_app_disabled(const char *app_id, bool value, uid_t uid)`
- L844: `EXPORT_API int notification_setting_db_update_pkg_disabled(const char *pkg_id, bool value, uid_t uid)`


### `src/notification/src/notification_shared_file.c` — Public — 6 APIs

**Functions**

- L623: `EXPORT_API void notification_remove_private_sharing_target_id( const char *sender, uid_t uid)`
- L656: `EXPORT_API void notification_add_private_sharing_target_id(pid_t pid, const char *sender, uid_t uid)`
- L763: `EXPORT_API bool notification_validate_private_sharing( notification_h updated_noti)`
- L811: `EXPORT_API void notification_calibrate_private_sharing( notification_h updated_noti, notification_h source_noti)`
- L1086: `EXPORT_API int notification_set_private_sharing(notification_h noti, uid_t uid)`
- L1332: `EXPORT_API void notification_remove_private_sharing( const char *src_app_id, int priv_id, uid_t uid)`


### `src/notification/src/notification_status.c` — Public — 3 APIs

**Functions**

- L74: `EXPORT_API int notification_status_monitor_message_cb_set(notification_status_message_cb callback, void *user_data)`
- L118: `EXPORT_API int notification_status_monitor_message_cb_unset(void)`
- L139: `EXPORT_API int notification_status_message_post(const char *message)`


### `src/notification/src/notification_viewer.c` — Public — 3 APIs

**Functions**

- L67: `EXPORT_API int notification_init_default_viewer()`
- L329: `EXPORT_API int notification_launch_default_viewer(int priv_id, notification_op_type_e status, uid_t uid)`
- L335: `EXPORT_API int notification_launch_default_viewer_without_candidate_process( int priv_id, notification_op_type_e status, uid_t uid)`

