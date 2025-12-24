(function($){
    $(document).ready(function(){
        var pollSelect = $('#id_poll');
        var districtSelect = $('#id_district');

        function setEmpty(){
            districtSelect.empty();
            districtSelect.append($('<option></option>').attr('value','').text('---------'));
        }

        function updateDistricts(pollId, selected){
            if(!pollId){
                setEmpty();
                return;
            }
            $.getJSON(window.location.origin + '/admin/api/candidate/districts-by-poll/', {poll_id: pollId})
            .done(function(data){
                districtSelect.empty();
                districtSelect.append($('<option></option>').attr('value','').text('---------'));
                $.each(data, function(i, item){
                    var opt = $('<option></option>').attr('value', item.id).text(item.name);
                    if(selected && selected === String(item.id)) opt.attr('selected', 'selected');
                    districtSelect.append(opt);
                });
            }).fail(function(){
                setEmpty();
            });
        }

        if(pollSelect.length && districtSelect.length){
            var selectedPoll = pollSelect.val();
            var selectedDistrict = districtSelect.val();
            updateDistricts(selectedPoll, selectedDistrict);

            pollSelect.change(function(){
                updateDistricts($(this).val(), null);
            });
        }
    });
})(django.jQuery);
