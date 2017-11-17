(function () {
    // 'use strict';
    $(document).ready(function () {
        $(".parent").click(function () {
            $(this).siblings('.child_' + this.id).toggle();
        });
    });
})();

