function ajaxgal() {
    $.ajax({
        url:      'api/list/images',
        method:   'GET',
        dataType: 'json',
        timeout:  10000,
        success:  function(data) {
            var images = data.images;
            images = images.slice(0,12)
            $('#ajaxgal').empty()
            for (var key in images) {
                $('<div>', { class: 'image' })
                        .append( $('<span>', { class: 'name', text: images[key] }))
                        .append( $('<img>', { src: '/api/image/scaled/220/'+images[key], title: images[key] }))
                        .appendTo('#ajaxgal');
            }
            $('div.image').click(function(){
                var imgname = $(this).children('span.name').text();
                $('#ajaxgal').empty();
                $('<div>', { class: 'image' })
                        .append( $('<span>', { class: 'name', text: imgname }))
                        .append( $('<img>', { src: '/api/image/scaled/600/'+imgname, title: imgname }))
                        .appendTo('#ajaxgal');
            });
        },
        error: function(xhr, textStatus, errorThrown){
            $('#ajaxgal')
                    .empty()
                    .append($('<div>', { class: 'note error', text: 'Sorry, could not connect to API server.' }));
        }
    });
};

      function onHashChange() { onLoad(); }
      function onLoad() {
        // get the unicode character from the #123 'hash' (preferred)
        var hash=location.hash;
        // or restore previous state (use HTML5 localStorage):
        var prev_pos = localStorage['prev_pos'];
        req_pos = hex2dec(hash.slice(3))
        // if req_pos >= 0 :
        if (req_pos+1) new_pos = req_pos;
        else if (prev_pos) new_pos = prev_pos;
        else new_pos = default_value;
        if (new_pos < 0 || new_pos > max_coarse + max_fine) new_pos = default_value
        //now we can be sure, the new_pos is in the range of possible values
        var coarse_pos, fine_pos;
        if (new_pos < offset()) { coarse_pos = 0; fine_pos = new_pos; }
        else if (new_pos > max_coarse + offset()) {coarse_pos = max_coarse; fine_pos = new_pos-coarse_pos; }
        else { coarse_pos = new_pos - offset(); fine_pos = offset(); }
        $( "#coarse_slider" ).slider( "value", coarse_pos );
        $( "#fine_slider" ).slider( "value", fine_pos);
      }