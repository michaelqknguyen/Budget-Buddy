/* Project specific Javascript goes here. */
(function($) {
  "use strict"; // Start of use strict

  $(document).on('click', '.confirm-delete', function(){
    return confirm('Are you sure you want to delete this?');
  })

})(jQuery); // End of use strict
