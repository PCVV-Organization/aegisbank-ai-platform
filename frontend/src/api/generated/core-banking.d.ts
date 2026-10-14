/**
 * Contract-aligned types for the synthetic core banking API.
 * Regenerate from a running OpenAPI document when `VITE_OPENAPI_URL` is available.
 */
export interface ServiceRequestCreateRequest {
  summary: string;
}
export interface ServiceRequestResponse {
  service_request_id: string;
  summary: string;
  status: string;
}
export interface ErrorResponse {
  code: string;
  message: string;
  correlation_id?: string;
}
export interface CustomerResponse {
  customer_id: string;
  display_name: string;
}
export interface LoanResponse {
  loan_id: string;
  customer_id: string;
  status: string;
}
export interface InstallmentResponse {
  loan_id: string;
  due_date: string;
  amount: number;
  currency: string;
}
