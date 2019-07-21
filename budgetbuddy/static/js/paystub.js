/* Project specific Javascript goes here. */
(function($) {
  "use strict"; // Start of use strict

  // Automatically generate flex contribution on paystub gross change
  $(document).on("change", "#moneyInput3", function() {
    var sum = 0;
    $(".budget .contribution").each(function(){
      sum += +$(this).val();
    });
    var grossPay = $("[name='gross_pay'").val();
    $(".total").val((grossPay-sum).toFixed(2));
  });

  // Automatically generate flex contribution on contribution change
  $(document).on("change", ".budget .contribution", function() {
    var sum = 0;
    $(".budget .contribution").each(function(){
      sum += +$(this).val();
    });
    var grossPay = $("[name='gross_pay'").val();
    $(".total").val((grossPay-sum).toFixed(2));
  });

  // Display Deposit total
  $(document).on("change", ".money .contribution", function() {
    var sum = 0;
    $(".money .contribution").each(function(){
      sum += +$(this).val();
    });
    $("#deposit-total").val("$"+(sum).toFixed(2));
  });

  $(document).on("submit", "form", function() {
    var sumContributions = 0;
    $(".budget .contribution").each(function(){
      sumContributions += +$(this).val();
    });
    sumContributions += +$(".total").val();

    var sumDeposits = 0;
    var sumDeposits = 0;
    $(".money .contribution").each(function(){
      sumDeposits += +$(this).val();
    });

    var grossPay = +$("[name='gross_pay'").val();

    if(grossPay.toFixed(2) !== sumContributions.toFixed(2)){
      alert('Sum of contributions must be equal to gross pay of paystub');
      return false;
    }

    if(grossPay.toFixed(2) !== sumDeposits.toFixed(2)){
      alert('Sum of deposits must be equal to gross pay of paystub');
      return false;
    }
  });

})(jQuery); // End of use strict