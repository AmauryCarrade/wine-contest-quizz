'use strict';

import jQuery from "jquery";

/**
 * Updates each file input field to be interactive, displaying their file name
 * when a file is selected.
 */
jQuery(function($)
{
    $('label.file-label').each(function()
    {
        let $this = $(this);
        $this.wrap('<div class="file has-name" />')
            .append('<div class="file-name">Ø</div>')
            .attr("title", gettext("Nothing selected yet. Click to choose a file."));

        let file_name = $this.find(".file-name");
        $this.find("input[type=file]").on('change', function()
        {
            file_name.text(this.files[0].name);
            $this.attr("title", interpolate(gettext("You selected “%s”. Click again to select another file."), [this.files[0].name]));
        });
    });
});
