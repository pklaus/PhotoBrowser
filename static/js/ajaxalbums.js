function ajaxalbums() {
    $.ajax({
        url:      'api/list/album_images',
        method:   'GET',
        dataType: 'json',
        timeout:  10000,
        success:  function(data) {
            var album_images = data;
            $('#ajaxalbums').empty();
            var min_epoch = 4294967295;
            var max_epoch = 0;
            for (var album in album_images) {
                epoch = album_images[album]['epoch'];
                if (epoch !== null) {
                    min_epoch = Math.min(min_epoch, epoch);
                    max_epoch = Math.max(max_epoch, epoch);
                }
                $('<div>', { class: 'album' })
                        .append( $('<span>', { class: 'name', text: album }))
                        .append( $('<span>', { class: 'epoch', text: epoch }))
                        .appendTo('#ajaxalbums');
            }
            $( "#slider" ).slider({
                range: true,
                min: min_epoch,
                max: max_epoch,
                values: [dateToEpoch(2005,5,5), dateToEpoch(2013,7,20)],
                step: 60*60*24,
                slide: sliding
            });
            $( "#amount" ).text( epochToDate($("#slider").slider("values", 0)) +
              " - " + epochToDate($("#slider").slider("values", 1)) );
        },
        error: function(xhr, textStatus, errorThrown){
            $('#ajaxalbums')
                    .empty()
                    .append($('<div>', { class: 'note error', text: 'Sorry, could not connect to API server.' }));
        }
    });
};

function sliding( event, ui ) {
    $( "#amount" ).text( epochToDate(ui.values[0]) +
      " - " + epochToDate(ui.values[1]) );
    $('.album').each(function(index) {
        var epoch = parseInt($('span.epoch', this).text());
        if (epoch < ui.values[0] || epoch > ui.values[1]) {
            $(this).css('display', 'none')
        } else {
            $(this).css('display', 'block')
        };
    });
}

function dateToEpoch(year, month, day) {
  return new Date(year, month-1, day).getTime() / 1000;
}
function epochToDate(epoch) {
  return new Date(epoch*1000).toISOString().substring(0,10);
}
