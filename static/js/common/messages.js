'use strict';

import jQuery from "jquery";

jQuery(function ($)
{
    $('article.message button.delete').on('click', function ()
    {
        let $message = $(this).parent().parent();

        $message.fadeOut('fast', function()
        {
            let $messages_container = $message.parent();
            let $messages_article = $message.parent().parent();

            $message.remove();

            if ($messages_container.children().length === 0)
            {
                $messages_article.remove();
            }
        });
    });
});
