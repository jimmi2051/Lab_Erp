jQuery.extend(jQuery.fn.dataTableExt.oSort, {
    "formatted-num-pre": function (a) {
        a = (a === "-" || a === "") ? 0 : a.replace(/[^\d\-\.]/g, "");
        return parseFloat(a);
    },

    "formatted-num-asc": function (a, b) {
        return a - b;
    },

    "formatted-num-desc": function (a, b) {
        return b - a;
    }
});
$(document).ready(function () {
    var table = $('#dataTables-example').dataTable({
        language: {
            paginate: {
                previous: "<i class='fa fa-arrow-left'></i>",
                next: "<i class='fa fa-arrow-right'></i>"
            },
            sProcessing: "Đang xử lý...",
            sLengthMenu: "Xem _MENU_ mục",
            sZeroRecords: "Không tìm thấy dòng nào phù hợp",
            sInfo: "Đang xem _START_ đến _END_ trong tổng số _TOTAL_ mục",
            sInfoEmpty: "Đang xem 0 đến 0 trong tổng số 0 mục",
            sInfoFiltered: "(được lọc từ _MAX_ mục)",
            sInfoPostFix: "",
            sSearch: "Tìm:",
            sUrl: "",
        },
        "dom": '<"toolbar">frtip',
        "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
        "columnDefs": [
            { "type": 'formatted-num', targets: 0 },
            { "type": 'formatted-num', targets: 2 },
            { "type": 'date-eu', targets: 3 }
        ],
        "order": [[ 0, "desc" ]],
        "processing": true,
        "ajax": {
            "processing": true,
            "url": "http://localhost:8000/merchant/orders?table=true",
            "dataSrc": ""
        },
    });
    var tool_bar = '';
    tool_bar += '<div class="col-xs-8 no_padding">';
    tool_bar += '<span>Trạng thái: </span>';
    tool_bar += '<select style="width:50%;display:inline-block;" id="select_type" class="form-control">';
    tool_bar += '<option>Tất cả</option>';
    tool_bar += '<option>Thành công</option>';
    tool_bar += '<option>Hủy bỏ</option>';
    tool_bar += '<option>Đặt hàng</option>';
    tool_bar += '<option>Đang gói hàng</option>';
    tool_bar += '<option>Đang vận chuyển</option>';
    tool_bar += '</select>';
    tool_bar += '</div>';
    $("div.toolbar").html(tool_bar);
    $('#select_type').change(function () {
        regExSearch = '^' + this.value + '$';
        if (this.value == "Tất cả") {
            table.api().columns(3).search('').draw();
        }
        else {
            table.api().columns(3).search(regExSearch, true, false).draw();
        }
    });
});

function change_state(order_id, state){
    $("#wrapper").css("display","none");
    $("#loader").css("display","block");
    $.ajax({
        url: 'http://localhost:8000/merchant/change_state/' + order_id + '/' + state,
        method: 'GET',
        success: function(response){
            if (response == 1){
                alert('Trạng thái đã thay đổi')
                $("#wrapper").css("display","block");
                $("#loader").css("display","none");
                window.location.replace('/merchant/order')
            }
            else{
                alert(response)
                $("#wrapper").css("display","block");
                $("#loader").css("display","none");
            }
        }
    })
}