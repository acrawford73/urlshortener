$(document).ready(function() {
    var existingTags = {{ form.tags.value|safe }}; // Load existing tags from Django
    console.log("Existing tags:", existingTags);

    $("#tag-input").select2({
        tags: true,  // Allow users to create new tags
        tokenSeparators: [','],  // Split tags by comma
        minimumInputLength: 1,  // Show suggestions after typing 1 character
        ajax: {
            url: "{% url 'tags-suggestions' %}",
            dataType: 'json',
            delay: 250,
            data: function(params) {
                console.log("Fetching suggestions for:", params.term);
                return { term: params.term };
            },
            processResults: function(data) {
                console.log("Received suggestions:", data);
                return { results: data };
            }
        },
        // Ensure Select2 sends tags as plain strings
        createTag: function(params) {
            return {id: String(params.term), text: String(params.term)};
        }
    });

    // Preload existing tags when editing
    if (existingTags) {
        var tagList = existingTags.map(tag => ({ id: tag, text: tag }));
        $("#tag-input").select2("data", tagList);
    }

    $('#tag-input').on('select2:select', function(e) {
        var data = e.params.data;
        console.log("Selected tag:", data);
        $('#selected-tags').append('<span class="badge bg-primary me-1">' + data.text + '</span>');
    });
});