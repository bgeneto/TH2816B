/**
 * Update logs via ajax in a defined interval
 */
(function poll() {
    setTimeout(function () {
        $.ajax({
            method: 'POST',
            url: '/ajax',
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({ 'fname': 'devices.log' }),
            success: function (data, textStatus, jqXHR) {
                if (data.contents === "undefined" || data.contents == false) {
                    return;
                }
                $('#devices_log').html(data.contents);
            },
            /* call poll again only if server responded last call
               avoids a bunch of queued Ajax requests in case of
               server not responding.
            */
            complete: poll
        });
    }, 3 * 1000); // set polling interval (seconds*1000 = microseconds)
})();