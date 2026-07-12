class axi_sequence extends uvm_sequence #(axi_seq_item);

    `uvm_object_utils(axi_sequence)

    function new(string name = "axi_sequence");
        super.new(name);
    endfunction

    virtual task body();
        // {% llm_fill "sequence_body" %}
        req = axi_seq_item::type_id::create("req");
        start_item(req);
        if (!req.randomize()) begin
            `uvm_fatal("SEQ", "Randomization failed")
        end
        finish_item(req);
// {% endllm_fill %}
    endtask

endclass