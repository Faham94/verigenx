class axi_lite_coverage extends uvm_subscriber #(axi_lite_seq_item);

    `uvm_component_utils(axi_lite_coverage)

    axi_lite_seq_item t;

    // Hit counters for functional points
    int hit_FP_001 = 0;

    // Auto-derived covergroups from functional points
    covergroup axi_lite_cg;
        option.per_instance = 1;

        
        // FP_001: Reset and initialisation
        // {% llm_fill "FP_001" %}
        cp_FP_001: coverpoint t.awvalid;
// {% endllm_fill %}
        
        
    endgroup

    function new(string name = "axi_lite_coverage", uvm_component parent = null);
        super.new(name, parent);
        axi_lite_cg = new();
    endfunction

    virtual function void write(axi_lite_seq_item t);
        this.t = t;
        // {% llm_fill "coverage_sample" %}
        axi_lite_cg.sample();
// {% endllm_fill %}

        // Manual hit counter updates
        if (t.awvalid) hit_FP_001++;
    endfunction

    virtual function void report_phase(uvm_phase phase);
        int fd;
        int total_points = 0;
        int covered_points = 0;
        real overall_coverage = 0.0;
        super.report_phase(phase);
        
        // Count covered points
        total_points++;
        if (hit_FP_001 > 0) covered_points++;
        
        if (total_points > 0) begin
            overall_coverage = (real'(covered_points) / real'(total_points)) * 100.0;
        end

        fd = $fopen("functional_coverage_report.json", "w");
        if (fd) begin
            $fwrite(fd, "{\n");
            $fwrite(fd, "  \"overall_functional_coverage\": %0.2f,\n", overall_coverage);
            $fwrite(fd, "  \"total_points\": %0d,\n", total_points);
            $fwrite(fd, "  \"covered_points\": %0d,\n", covered_points);
            $fwrite(fd, "  \"points\": {\n");
            $fwrite(fd, "    \"FP_001\": {\n");
            $fwrite(fd, "      \"description\": \"Reset and initialisation\",\n");
            $fwrite(fd, "      \"hit_count\": %0d,\n", hit_FP_001);
            $fwrite(fd, "      \"total_bins\": 1,\n");
            $fwrite(fd, "      \"coverage_percentage\": %0.2f\n", (hit_FP_001 > 0) ? 100.0 : 0.0);
            $fwrite(fd, "    }\n");
            $fwrite(fd, "  }\n");
            $fwrite(fd, "}\n");
            $fclose(fd);
            $display("[UVM_INFO] Dumped functional coverage report to functional_coverage_report.json. Overall coverage: %0.2f%%", overall_coverage);
        end else begin
            $display("[UVM_ERROR] Failed to open functional_coverage_report.json for writing");
        end
    endfunction

endclass