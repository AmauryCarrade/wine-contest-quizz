'use strict';

import jQuery from "jquery";

jQuery(function ($)
{
    function toggle_correction_block($block, animate)
    {
        $block.find('.card-header .card-header-icon .icon .fas')
            .toggleClass('fa-angle-down')
            .toggleClass('fa-angle-up');

        if (animate)
        {
            $block.find('.card-content').slideToggle('fast');
        }
        else
        {
            $block.find('.card-content').toggle();
        }
    }

    let $corrections = $("#quizz-report article.question-correction");

    $corrections.each(function()
    {
        if ($(this).data('result') === 'PERFECT')
        {
            toggle_correction_block($(this));
        }
    });

    $corrections.find('.card-header').on('click', function(e)
    {
         toggle_correction_block($(this).parent(), true);
         e.preventDefault();
    });
});
