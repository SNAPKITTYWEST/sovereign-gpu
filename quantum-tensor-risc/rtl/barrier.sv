// ============================================================================
// Sovereign GPU — Barrier Synchronization Unit
// Counts arrivals and releases when all SMs reach barrier
// ============================================================================

module barrier #(
    parameter SM_COUNT = 4
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic [SM_COUNT-1:0] sm_arrive,
    input  logic [SM_COUNT-1:0] sm_release_ack,
    output logic [SM_COUNT-1:0] sm_released,
    output logic        all_arrived
);

    logic [SM_COUNT-1:0] arrived;
    logic [$clog2(SM_COUNT):0] arrive_count;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            arrived <= {SM_COUNT{1'b0}};
            arrive_count <= 0;
            sm_released <= {SM_COUNT{1'b0}};
        end else begin
            for (int i = 0; i < SM_COUNT; i++) begin
                if (sm_arrive[i] && !arrived[i]) begin
                    arrived[i] <= 1'b1;
                    arrive_count <= arrive_count + 1;
                end
                if (sm_release_ack[i])
                    arrived[i] <= 1'b0;
            end

            if (arrive_count == SM_COUNT) begin
                sm_released <= {SM_COUNT{1'b1}};
                arrive_count <= 0;
            end

            for (int i = 0; i < SM_COUNT; i++) begin
                if (sm_released[i] && sm_release_ack[i])
                    sm_released[i] <= 1'b0;
            end
        end
    end

    assign all_arrived = (arrive_count == SM_COUNT);

endmodule
