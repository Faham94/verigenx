class uart_sequence extends uvm_sequence #(uart_seq_item);

    `uvm_object_utils(uart_sequence)

    function new(string name = "uart_sequence");
        super.new(name);
    endfunction

    virtual task body();
        // {% llm_fill "sequence_body" %}
        req = uart_seq_item::type_id::create("req");
        start_item(req);
        if (!req.randomize()) begin
            `uvm_fatal("SEQ", "Randomization failed")
        end
        finish_item(req);
// {% endllm_fill %}
    endtask

endclass