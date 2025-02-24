$(document).ready(function() {
	var existingTags = {{ form.tags.value|safe }}; // Load existing tags from Django
	$("#tags-input").select2({
		tags: true,  // Allow users to create new tags
		tokenSeparators: [','],  // Split tags by comma
		minimumInputLength: 1,  // Show suggestions after typing 1 character
		ajax: {
			url: "{% url 'tags-autocomplete' %}",
			dataType: 'json',
			delay: 250,
			data: function(params) {
				return { term: params.term };
			},
			processResults: function(data) {
				return { results: data.map(tag => ({ id: tag.name, text: tag.text })) };
				//return { results: data };
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
		$("#tags-input").select2("data", tagList);
	}

	$(document).on("click", ".tag-suggestion", function (e) {
		e.preventDefault();
		let tag = $(this).text();
		$("#selected-tags").append(`<span class="badge bg-primary me-1">${tag}</span>`);
		$("#tag-input").val("");
		$("#tag-suggestions").empty();
	});
});

