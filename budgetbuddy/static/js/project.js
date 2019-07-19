/* Project specific Javascript goes here. */
(function($) {
  "use strict"; // Start of use strict

  $(document).on('click', '.confirm-delete', function(){
    return confirm('Are you sure you want to delete this?');
  })

})(jQuery); // End of use strict

// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#transTable').DataTable({
    "order": [[ 0, "desc" ]]
  });

  $('#moneyInput').blur(function() {
    this.value = parseFloat(this.value).toFixed(2);
  });

  $('#moneyInput2').blur(function() {
    this.value = parseFloat(this.value).toFixed(2);
  });
});
