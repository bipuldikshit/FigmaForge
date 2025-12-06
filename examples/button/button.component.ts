import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * ButtonComponent
 * Generated from Figma component: Primary Button
 * 
 * AUTO-GENERATED - Do not modify the @Component decorator and class signature.
 * You can add custom methods and logic below the auto-generated section.
 */
@Component({
    selector: 'app-button',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './button.component.html',
    styleUrls: ['./button.component.scss']
})
export class ButtonComponent {
    // ==================== AUTO-GEN-START ====================
    // Auto-generated @Input properties

    @Input() icon: string = '';
    @Input() iconUrl: string = '';
    @Input() label: string = '';
    @Input() text: string = '';

    // ==================== AUTO-GEN-END ====================

    // Add your custom methods and logic below

    constructor() {
        // Component initialization
    }

    // Example custom method
    handleClick(): void {
        console.log('Button clicked:', this.text || this.label);
    }
}
