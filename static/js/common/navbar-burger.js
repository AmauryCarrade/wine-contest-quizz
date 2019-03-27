'use strict';

import jQuery from "jquery";

/**
 * Opens or closes the menu when the burger is clicked, for mobile devices.
 */
jQuery(function ($)
{
    $('.navbar-burger').on('click', function()
    {
        // Get the target from the "data-target" attribute
        const target = $(this).data('target');
        const $target = $('#' + target);

        // Toggle the "is-active" class on both the "navbar-burger" and the "navbar-menu"
        $(this).toggleClass('is-active');
        $target.toggleClass('is-active');
    });
});
