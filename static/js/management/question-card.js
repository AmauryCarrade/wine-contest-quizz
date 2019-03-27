'use strict';

import jQuery from "jquery";

jQuery(function($)
{
    $('.is-overflowing-tags-toggler').on('click', function (e)
    {
        e.preventDefault();
        $(this).parent().find('.tag.is-overflowing-tag').toggleClass("is-hidden");

        let cur_text = $(this).text();
        let cur_title = $(this).attr("title");

        $(this).text($(this).data("other-text"))
               .attr("title", $(this).data("other-title"))
               .data("other-text", cur_text)
               .data("other-title", cur_title);
    });
});
